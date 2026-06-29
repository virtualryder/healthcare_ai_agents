#!/usr/bin/env bash
# Smoke-test the deployed golden path. Usage: ./smoke_test.sh <stack-name>
set -uo pipefail
STACK="${1:-hpp-gp01-dev}"
URL=$(aws cloudformation describe-stacks --stack-name "$STACK" --query "Stacks[0].Outputs[?OutputKey=='GatewayUrl'].OutputValue" --output text)
echo "Gateway: $URL"
echo "1) /ping (unauthenticated health):"
curl -s "$URL/ping"; echo
cat <<NOTE

2) Authenticated tool call (governed): obtain a Cognito JWT for a user whose
   custom:hpp_role is DENIALS_SPECIALIST, then:

   TOKEN=<cognito id token>
   # READ (allowed):
   curl -s -H "Authorization: $TOKEN" -XPOST "$URL/tool/pas/get_claim" \\
     -d '{"args":{"claim_ref":"CLM-2026-55810"}}'
   # HIGH-RISK WRITE without approval -> PENDING_APPROVAL (the human gate holds):
   curl -s -H "Authorization: $TOKEN" -XPOST "$URL/tool/payer/submit_appeal" \\
     -d '{"args":{"claim_ref":"CLM-2026-55810","level":1}}'
   # WITHHELD tool (claim submission) -> DENY (deny-by-default):
   curl -s -H "Authorization: $TOKEN" -XPOST "$URL/tool/clearinghouse/submit_claim" \\
     -d '{"args":{"claim_ref":"CLM-1"}}'

Expected: get_claim -> ALLOW; submit_appeal -> PENDING_APPROVAL; submit_claim -> DENY.
Every attempt is written to the append-only audit table ($STACK AuditTable).
NOTE
