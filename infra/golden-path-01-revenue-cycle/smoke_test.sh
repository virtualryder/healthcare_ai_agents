#!/usr/bin/env bash
# Smoke-test the deployed golden path. Usage: ./smoke_test.sh <stack-name>
# Proves the GOVERNANCE controls end-to-end on the deployed API, not just liveness:
# deny-by-default, the human gate, the approval-bypass being CLOSED, two-person
# (separation-of-duties) approval, single-use replay protection, and the audit trail.
set -uo pipefail
STACK="${1:-hpp-gp01-dev}"
out() { aws cloudformation describe-stacks --stack-name "$STACK" \
  --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text; }
URL=$(out GatewayUrl); APPROVALS=$(out ApprovalsUrl); AUDIT=$(out AuditTableName)
echo "Gateway:   $URL"
echo "Approvals: $APPROVALS"
echo "1) /ping (unauthenticated health):"
curl -s "$URL/ping"; echo
echo
echo "1b) Network isolation — must report BLOCKED (no public-internet egress):"
EG=$(out EgressCheckUrl); curl -s "$EG"; echo
echo "   ^ blocked:true => the runtime has no route to the internet (PHI cannot egress)."
cat <<NOTE

Obtain TWO Cognito id tokens:
  REQ_TOKEN  = a user whose custom:hpp_role = DENIALS_SPECIALIST   (the requester)
  REV_TOKEN  = a DIFFERENT user with an approver role               (the reviewer)

2) READ (allowed):
   curl -s -H "Authorization: \$REQ_TOKEN" -XPOST "$URL/tool/pas/get_claim" \\
     -d '{"args":{"claim_ref":"CLM-2026-55810"}}'                      # -> ALLOW

3) HIGH-RISK WRITE, no approval -> PENDING_APPROVAL (human gate holds):
   curl -s -H "Authorization: \$REQ_TOKEN" -XPOST "$URL/tool/payer/submit_appeal" \\
     -d '{"args":{"claim_ref":"CLM-2026-55810","level":1}}'           # -> PENDING_APPROVAL

4) APPROVAL-BYPASS CHECK — requester forges a reviewer in the body. With
   AUTH_REQUIRE_BOUND_APPROVAL=1 the demo path is CLOSED, so this must NOT execute:
   curl -s -H "Authorization: \$REQ_TOKEN" -XPOST "$URL/tool/payer/submit_appeal" \\
     -d '{"args":{"claim_ref":"CLM-2026-55810","level":1},
          "approval":{"approved":true,"reviewer":{"sub":"made-up"}}}'  # -> PENDING_APPROVAL (blocked)

5) TWO-PERSON APPROVAL — the REVIEWER authenticates to the reviewer service and mints a
   bound, single-use token for this exact claim+tool+requester:
   TOK=\$(curl -s -H "Authorization: \$REV_TOKEN" -XPOST "$APPROVALS" \\
     -d '{"tool":"payer.submit_appeal","requester_sub":"<REQUESTER_SUB>",
          "args":{"claim_ref":"CLM-2026-55810","level":1}}' | jq -r .token)
   # Now the requester submits WITH the bound token:
   curl -s -H "Authorization: \$REQ_TOKEN" -XPOST "$URL/tool/payer/submit_appeal" \\
     -d "{\"args\":{\"claim_ref\":\"CLM-2026-55810\",\"level\":1},\"approval\":{\"token\":\"\$TOK\"}}"  # -> ALLOW (once)

6) REPLAY CHECK — submit the SAME token again -> single-use guard rejects it:
   curl -s -H "Authorization: \$REQ_TOKEN" -XPOST "$URL/tool/payer/submit_appeal" \\
     -d "{\"args\":{\"claim_ref\":\"CLM-2026-55810\",\"level\":1},\"approval\":{\"token\":\"\$TOK\"}}"  # -> PENDING_APPROVAL (replay blocked)

7) WITHHELD tool (claim submission) -> DENY (deny-by-default):
   curl -s -H "Authorization: \$REQ_TOKEN" -XPOST "$URL/tool/clearinghouse/submit_claim" \\
     -d '{"args":{"claim_ref":"CLM-1"}}'                              # -> DENY

Expected: 2 ALLOW(read), 3 PENDING, 4 PENDING(bypass blocked), 5 ALLOW(approved),
          6 PENDING(replay blocked), 7 DENY. Every attempt is written to the
          append-only audit table: $AUDIT
Network: GET /egress-check must return blocked:true (private subnets, no IGW/NAT).
NOTE
