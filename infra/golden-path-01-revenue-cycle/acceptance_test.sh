#!/usr/bin/env bash
# Clean-account ACCEPTANCE TEST for the HPP golden path. Run against a freshly deployed stack;
# it proves the deployed system ENFORCES the controls (not just models them) and exits non-zero
# on any failure. Sequence:
#   network isolation -> read ALLOW -> write PENDING -> approval-bypass BLOCKED ->
#   self-approval BLOCKED -> two-person approval ALLOW once -> replay BLOCKED -> tampered-args
#   BLOCKED -> withheld tool DENY -> async workflow approve+finalize -> durable audit present.
#
# Usage:  ./acceptance_test.sh <stack-name> [region]
# Requires: awscli v2, curl, jq, and credentials for the target (sandbox) account.
set -uo pipefail
STACK="${1:-hpp-gp01-dev}"; REGION="${2:-${AWS_REGION:-us-east-1}}"
PASS=0; FAIL=0
ok(){ echo "  PASS: $1"; PASS=$((PASS+1)); }
bad(){ echo "  FAIL: $1"; FAIL=$((FAIL+1)); }
check(){ # check <description> <expected-substring> <actual>
  if echo "$3" | grep -q "$2"; then ok "$1 (got: $(echo "$3" | tr -d '\n' | cut -c1-80))"
  else bad "$1 — expected '$2' in: $(echo "$3" | tr -d '\n' | cut -c1-160)"; fi; }
out(){ aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text; }

echo "== Resolving stack outputs =="
URL=$(out GatewayUrl); APPROVALS=$(out ApprovalsUrl); EGRESS=$(out EgressCheckUrl)
POOL=$(out UserPoolId); CLIENT=$(out UserPoolClientId)
AUDIT=$(out AuditTableName); HITL=$(out HitlTableName); SM=$(out StateMachineArn)
[ -n "$URL" ] || { echo "no stack outputs — is $STACK deployed?"; exit 2; }

echo "== Federating two identities (requester + reviewer) =="
PW='Hpp!Accept1234'; REQ="acc-requester"; REV="acc-reviewer"
for u in "$REQ:DENIALS_SPECIALIST" "$REV:reviewer"; do
  USERNAME="${u%%:*}"; ROLE="${u##*:}"
  aws cognito-idp admin-create-user --user-pool-id "$POOL" --username "$USERNAME" \
    --message-action SUPPRESS --user-attributes Name=custom:hpp_role,Value="$ROLE" --region "$REGION" >/dev/null 2>&1
  aws cognito-idp admin-set-user-password --user-pool-id "$POOL" --username "$USERNAME" \
    --password "$PW" --permanent --region "$REGION" >/dev/null
done
tok(){ aws cognito-idp admin-initiate-auth --user-pool-id "$POOL" --client-id "$CLIENT" \
  --auth-flow ADMIN_USER_PASSWORD_AUTH --auth-parameters USERNAME="$1",PASSWORD="$PW" \
  --region "$REGION" --query 'AuthenticationResult.IdToken' --output text; }
REQ_TOKEN=$(tok "$REQ"); REV_TOKEN=$(tok "$REV")
REQ_SUB=$(aws cognito-idp admin-get-user --user-pool-id "$POOL" --username "$REQ" --region "$REGION" \
  --query 'UserAttributes[?Name==`sub`].Value' --output text)
ARGS='{"claim_ref":"CLM-2026-55810","level":1}'

echo "== 1. Network isolation =="
check "no public-internet egress" '"blocked": *true' "$(curl -s "$EGRESS")"

echo "== 2. Read is allowed =="
check "pas.get_claim ALLOW" 'ALLOW' "$(curl -s -H "Authorization: $REQ_TOKEN" -XPOST "$URL/tool/pas/get_claim" -d '{"args":{"claim_ref":"CLM-2026-55810"}}')"

echo "== 3. High-risk write without approval pends =="
check "submit_appeal PENDING" 'PENDING_APPROVAL' "$(curl -s -H "Authorization: $REQ_TOKEN" -XPOST "$URL/tool/payer/submit_appeal" -d "{\"args\":$ARGS}")"

echo "== 4. Approval-bypass blocked (fabricated reviewer) =="
check "fabricated reviewer BLOCKED" 'PENDING_APPROVAL' "$(curl -s -H "Authorization: $REQ_TOKEN" -XPOST "$URL/tool/payer/submit_appeal" -d "{\"args\":$ARGS,\"approval\":{\"approved\":true,\"reviewer\":{\"sub\":\"made-up\"}}}")"

echo "== 5. Self-approval blocked at the reviewer service =="
check "self-approval 403" 'separation of duties' "$(curl -s -H "Authorization: $REQ_TOKEN" -XPOST "$APPROVALS" -d "{\"tool\":\"payer.submit_appeal\",\"args\":$ARGS,\"requester_sub\":\"$REQ_SUB\"}")"

echo "== 6. Two-person approval -> ALLOW once =="
TOK=$(curl -s -H "Authorization: $REV_TOKEN" -XPOST "$APPROVALS" -d "{\"tool\":\"payer.submit_appeal\",\"args\":$ARGS,\"requester_sub\":\"$REQ_SUB\"}" | jq -r .token)
check "approved write ALLOW" 'ALLOW' "$(curl -s -H "Authorization: $REQ_TOKEN" -XPOST "$URL/tool/payer/submit_appeal" -d "{\"args\":$ARGS,\"approval\":{\"token\":\"$TOK\"}}")"

echo "== 7. Replay blocked =="
check "replay BLOCKED" 'PENDING_APPROVAL' "$(curl -s -H "Authorization: $REQ_TOKEN" -XPOST "$URL/tool/payer/submit_appeal" -d "{\"args\":$ARGS,\"approval\":{\"token\":\"$TOK\"}}")"

echo "== 8. Tampered arguments blocked =="
TOK2=$(curl -s -H "Authorization: $REV_TOKEN" -XPOST "$APPROVALS" -d "{\"tool\":\"payer.submit_appeal\",\"args\":$ARGS,\"requester_sub\":\"$REQ_SUB\"}" | jq -r .token)
check "tampered args BLOCKED" 'PENDING_APPROVAL' "$(curl -s -H "Authorization: $REQ_TOKEN" -XPOST "$URL/tool/payer/submit_appeal" -d "{\"args\":{\"claim_ref\":\"CLM-OTHER-99999\",\"level\":1},\"approval\":{\"token\":\"$TOK2\"}}")"

echo "== 9. Withheld tool denied (deny-by-default) =="
check "submit_claim DENY" 'DENY' "$(curl -s -H "Authorization: $REQ_TOKEN" -XPOST "$URL/tool/clearinghouse/submit_claim" -d '{"args":{"claim_ref":"CLM-1"}}')"

echo "== 10. Async workflow: start -> human gate -> approve -> finalize =="
EXEC=$(aws stepfunctions start-execution --state-machine-arn "$SM" --region "$REGION" \
  --input "{\"claim_ref\":\"CLM-2026-55810\",\"user_claims\":{\"sub\":\"$REQ_SUB\",\"custom:hpp_role\":\"DENIALS_SPECIALIST\"}}" \
  --query executionArn --output text)
RID=""; for _ in $(seq 1 15); do
  RID=$(aws dynamodb scan --table-name "$HITL" --region "$REGION" \
    --filter-expression "#s = :p" --expression-attribute-names '{"#s":"status"}' \
    --expression-attribute-values '{":p":{"S":"PENDING"}}' \
    --query 'Items[0].review_id.S' --output text 2>/dev/null)
  [ -n "$RID" ] && [ "$RID" != "None" ] && break; sleep 2; done
if [ -n "$RID" ] && [ "$RID" != "None" ]; then
  curl -s -H "Authorization: $REV_TOKEN" -XPOST "$APPROVALS" -d "{\"review_id\":\"$RID\"}" >/dev/null
  ST=""; for _ in $(seq 1 20); do
    ST=$(aws stepfunctions describe-execution --execution-arn "$EXEC" --region "$REGION" --query status --output text)
    [ "$ST" != "RUNNING" ] && break; sleep 3; done
  check "workflow SUCCEEDED after approval" 'SUCCEEDED' "$ST"
else bad "workflow never reached the human gate (no PENDING review)"; fi

echo "== 11. Durable audit present =="
N=$(aws dynamodb scan --table-name "$AUDIT" --region "$REGION" --select COUNT --query Count --output text 2>/dev/null)
if [ "${N:-0}" -gt 0 ] 2>/dev/null; then ok "append-only audit has $N records"; else bad "audit table empty"; fi

echo; echo "== ACCEPTANCE: $PASS passed, $FAIL failed =="
exit $([ "$FAIL" -eq 0 ] && echo 0 || echo 1)
