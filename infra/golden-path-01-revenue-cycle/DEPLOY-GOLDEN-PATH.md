# Golden Path — Agent 01 Revenue-Cycle & Denial (one-command deploy)

The fastest path from an empty AWS account to a **running, governed** Agent-01 API whose tool
route is enforced through the MCP gateway (deny-by-default → bound approval → scoped token →
append-only PHI-masked audit). Fixture mode (no PHI, no live connectors). **An AWS BAA must be
executed before any PHI.**

## Prerequisites
- AWS CLI + **AWS SAM CLI** installed and credentials configured.
- Amazon Bedrock model access enabled in the Region (for live drafting later).
- See `../../docs/AWS-ACCOUNT-PREREQUISITES.md`.

## Deploy (one path)
```bash
cd infra/golden-path-01-revenue-cycle
./build.sh                       # vendors platform_core, then `sam build`
sam deploy --guided              # first time (pick a stack name, e.g. hpp-gp01-dev); then just `sam deploy`
```
What it stands up: a Cognito user pool (with `custom:hpp_role`), an HTTP API with a **Cognito JWT
authorizer**, the **governed connector Lambda** (the tool route runs through the gateway), a
**customer-managed KMS CMK**, and **append-only audit + HITL** DynamoDB tables (PITR, KMS).

## Smoke test (proves the governance holds)
```bash
./smoke_test.sh hpp-gp01-dev
```
- `GET /ping` → healthy.
- Seed a Cognito user with `custom:hpp_role=DENIALS_SPECIALIST`, get an ID token, then:
  - `POST /tool/pas/get_claim` → **ALLOW** (read).
  - `POST /tool/payer/submit_appeal` (no approval) → **PENDING_APPROVAL** (the human gate holds).
  - `POST /tool/clearinghouse/submit_claim` → **DENY** (withheld from the agent — a biller submits).
- Every attempt lands in the append-only audit table.

## The async denial workflow (Step Functions)
The deploy also creates a **Standard state machine** (`StateMachineArn` output) that runs the real
denial pipeline — no `Pass` placeholders:

`LoadClaim → AnalyzeDenial → (appealable?) → GatherEvidence → DraftAppeal → ComplianceCheck →
(grounded?) → HumanReviewGate [waitForTaskToken] → (approved?) → Finalize → SendToOutbox`

Every task runs through the governed gateway (`WorkflowFn`), so the orchestration inherits
deny-by-default authz, scoped tokens, and the append-only audit. The human gate uses
`waitForTaskToken`: the workflow records `{review_id, task_token, pending_write}` to the HITL
table and pauses. The approved appeal is **exported to a controlled SQS outbox** (`AppealOutboxUrl`)
for a biller to transmit — it is not auto-submitted to the payer.

Run it end-to-end:

```bash
SM=$(aws cloudformation describe-stacks --stack-name hpp-gp01-dev \
  --query "Stacks[0].Outputs[?OutputKey=='StateMachineArn'].OutputValue" --output text)
HITL=$(aws cloudformation describe-stacks --stack-name hpp-gp01-dev \
  --query "Stacks[0].Outputs[?OutputKey=='HitlTableName'].OutputValue" --output text)
APPROVALS=$(aws cloudformation describe-stacks --stack-name hpp-gp01-dev \
  --query "Stacks[0].Outputs[?OutputKey=='ApprovalsUrl'].OutputValue" --output text)

# 1) start a denial workflow for a requester (DENIALS_SPECIALIST)
aws stepfunctions start-execution --state-machine-arn "$SM" \
  --input '{"claim_ref":"CLM-2026-55810","user_claims":{"sub":"u-requester","custom:hpp_role":"DENIALS_SPECIALIST"}}'

# 2) the workflow pauses at HumanReviewGate — find the PENDING review_id
aws dynamodb scan --table-name "$HITL" --filter-expression "#s = :p" \
  --expression-attribute-names '{"#s":"status"}' --expression-attribute-values '{":p":{"S":"PENDING"}}'

# 3) a DIFFERENT user (reviewer, approver role) approves by review_id — the reviewer service
#    mints a bound token AND resumes the execution (SendTaskSuccess):
curl -s -H "Authorization: $REV_TOKEN" -XPOST "$APPROVALS" -d '{"review_id":"<REVIEW_ID>"}'

# 4) execution resumes -> Finalize (governed write w/ bound token) -> SendToOutbox.
#    Confirm an approved appeal landed on the controlled outbox queue.
```

Self-approval (reviewer == requester), a fabricated reviewer, a replayed token, or tampered args
are all rejected — the same enforcement proven by `tests/` and `platform_core/tests/test_acceptance_enforcement.py`.

## Network isolation (data residency)
The runtime Lambdas (`ConnectorFn`, `ReviewerFn`) are VPC-attached to **private subnets with no
internet route** — the route table has only the local route (no Internet Gateway, no NAT). Every
AWS dependency is reached over a VPC endpoint that lives inside the VPC:

- **DynamoDB** (audit / HITL / jti) — gateway endpoint, account-scoped endpoint policy.
- **KMS, CloudWatch Logs, STS** — interface endpoints (PrivateLink), reachable only from the
  runtime security group on 443.
- **Bedrock runtime** — interface endpoint created only when `BedrockModelArn` is set, with an
  endpoint policy scoped to that model ARN and this account. Inference stays in-account.

Because there is no IGW/NAT and no `0.0.0.0/0` route, PHI cannot egress to the public internet.
Verify after deploy:

```bash
curl -s "$(aws cloudformation describe-stacks --stack-name hpp-gp01-dev \
  --query "Stacks[0].Outputs[?OutputKey=='EgressCheckUrl'].OutputValue" --output text)"
# expect: {"public_internet_egress":"BLOCKED","blocked":true,"verdict":"PASS — no public egress path"}
```

A `blocked:false` / `REACHABLE` result means the isolation is NOT in place and the deploy must be rejected.

## Teardown
```bash
./teardown.sh hpp-gp01-dev
```

## Going live (engagement)
Set `AUTH_REQUIRE_JWT=1` + JWKS (already verified at the edge here); swap `CONNECTOR_MODE=sandbox` (the resilient adapter: OAuth2/bearer auth, idempotency keys on
writes, retry/backoff, timeouts, circuit breaker, write reconciliation, lineage) and point
`<KIND>_BASE_URL` (+ `<KIND>_API_KEY` or `<KIND>_TOKEN_URL`/`_CLIENT_ID`/`_CLIENT_SECRET`) at the
real EHR/clearinghouse/payer sandbox (`CONNECTOR_MODE=live` is the bare reference adapter) (see `../../platform_core/.../connectors/live.py`
and the reference live façade in `../../01-revenue-cycle-denial-agent/demo/demo_live.py`); attach a
Bedrock Guardrail; complete the go-live checklist in `../../docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`.
