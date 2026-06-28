# Threat Model — HPP AI Agent Suite

Scope: the governed control plane and a single agent's request path (the same pattern repeats
for all eight). Method: trust boundaries + STRIDE + LLM-specific abuse cases. Every mitigation
points to code or IaC; residual risk is named honestly.

## Trust boundaries
```
[ Workforce user / member ]  --TLS-->  CloudFront + WAF + Shield      (B1 edge)
   -->  API Gateway + Cognito (federated IdP -> short-lived RS256 JWT) (B2 identity)
   -->  Agent runtime (Step Functions/Lambda or Fargate) private subnet (B3 compute)
   -->  MCP authorization gateway (re-verifies JWT, decides, mints scoped token, audits) (B4 control plane)
   -->  Connector Lambda  -->  System of record (EHR/clearinghouse/payer)  (B5 data egress)
   -->  Amazon Bedrock + Guardrails via VPC endpoint  (B6 model)
   -->  DynamoDB append-only audit / HITL · S3 Object Lock WORM · KMS  (B7 data tier)
```
Crossing any boundary is authenticated, authorized, and audited. The agent never holds a
standing credential to a system of record — it receives a per-call scoped token.

## Assets
PHI (claims, charts, member data); the audit trail; signing keys (JWT, approval, scoped-token);
the authorization policy; Bedrock Guardrail config; reviewer identities.

## Abuse cases and mitigations
| # | Threat (STRIDE / LLM) | Mitigation | Where |
|---|---|---|---|
| T1 | **Spoofed identity / forged role** (S) | RS256/JWKS verification; client roles never trusted; alg-confusion guard rejects `none`/`HS*` | `jwt_verify.py`; test_security_controls |
| T2 | **Agent over-reach** — calls a tool it shouldn't (E) | Deny-by-default; permitted ⇔ agent grant ∩ user entitlement; consequential tools withheld | `mcp_gateway/policy.py`; gateway tests |
| T3 | **Privilege escalation via the human** (E) | Agent can never exceed the acting user's entitlements (intersection) | `policy.decide` |
| T4 | **Autonomous consequential action** (E) | Submit-claim / issue-determination withheld from all agents; framework-enforced human gate | `policy.py`, graph `interrupt_before` |
| T5 | **Approval replay / retarget** (T,R) | Bound, single-use, SoD approval token tied to exact tool+args; jti replay guard; expiry | `approvals.py`; test_security_controls |
| T6 | **Self-approval** (R) | Separation of duties — reviewer ≠ requester at mint and verify, even on the demo path | `approvals.py`, gateway `_approval_ok` |
| T7 | **Audit tampering / repudiation** (T,R) | Append-only hash chain (`verify_chain`); prod conditional writes + IAM deny + S3 Object Lock WORM | `audit.py`, `audit_sinks.py`, `data.yaml` |
| T8 | **PHI leakage to logs / external AI** (I) | Fail-closed PHI masking at every audit/trace boundary; in-account Bedrock (no egress); Guardrails | `phi.py`, `llm_factory.py`, `tracing.py` |
| T9 | **Prompt injection → tool abuse** (LLM01) | Authorization is structural, not prompt-based — injected "approve this" cannot grant a withheld tool | `governance/redteam`, gateway |
| T10 | **Hallucinated clinical/financial claim** (LLM09) | Grounding verification fails any code/amount/policy not traceable to source | `governance/grounding.py` |
| T11 | **Model/prompt drift** | Hash-pinned prompt registry; CI fails on un-bumped change | `governance/prompt_registry.py`, `test_all_prompts_pinned` |
| T12 | **Algorithmic bias in UM / risk** | Four-fifths fairness screen on flag/rank; adverse action never automated | `governance/fairness`, agents 05/07 |
| T13 | **Secret/credential theft** (I) | No standing service accounts; scoped per-call tokens; secrets via Secrets Manager/KMS | `tokens.py`, `secrets.py` |
| T14 | **DoS / cost-bomb on the model** (D) | WAF rate-limit + Shield at edge; Bedrock quotas; queue-based backpressure (native mode) | `edge`/infra, runbooks |
| T15 | **42 CFR Part 2 / sensitive-data disclosure** (I) | Consent check before sensitive disclosure; escalate without consent | agents 03/07 `check_consent` |

## Residual risk (named honestly)
The Python gateway is a **reference model** of the production AgentCore Gateway / API Gateway +
Cedar authorizer — the production authorizer must be tested, not just this analog. Live
connectors, IdP integration, Guardrail tuning against customer data, penetration testing, and
HITRUST/SOC 2 authorization are customer-engagement work (see
`PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`). The LLM is non-deterministic; grounding +
the human gate are the compensating controls — not a guarantee of correctness.
