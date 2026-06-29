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
Set `AUTH_REQUIRE_JWT=1` + JWKS (already verified at the edge here); swap `CONNECTOR_MODE=live`
and point the connectors at the real EHR/clearinghouse/payer (see `../../platform_core/.../connectors/live.py`
and the reference live façade in `../../01-revenue-cycle-denial-agent/demo/demo_live.py`); attach a
Bedrock Guardrail; complete the go-live checklist in `../../docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`.
