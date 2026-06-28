# Production Readiness & Shared Responsibility (read before any production decision)

**Honest status: this is a production-shaped accelerator, not an authorized, production-ready
system — and it doesn't claim to be.** That honesty is the point: it embeds the governance
controls usually retrofitted, which de-risks the path to production, but real work remains and
most of it is the customer's.

## Why it gives confidence (verifiable today)
Consequential actions withheld in code + tested · framework-enforced human gate · deny-by-default
least-privilege intersection · **cryptographic JWT verification** · **bound single-use
separation-of-duties approvals** · **hash-chained append-only audit** + WORM · PHI masking ·
complete AWS security architecture mapped to your regimes · no lock-in (readable Python, CFN +
Terraform) · a no-API-key test suite incl. control-plane negative-case tests (JWT, approvals,
audit chain).

## What must still be built / authorized before go-live (stated plainly)
- **Integrations are fixtures** — no live connectors yet to EHR/FHIR, clearinghouse, payer
  portals, Amazon Connect. Each must be built and validated (usually the largest line item).
- **No HITRUST/SOC 2 authorization** and **no third-party security testing** (pen test). The
  Python gateway is a *reference model* of the authorization; the production AgentCore Gateway /
  API Gateway + Cedar authorizer must be tested, not just the analog.
- **AWS BAA** must be executed before any PHI is processed.
- **Model-risk validation**, Guardrail/red-team tuning against your data, accessibility (axe-core
  + manual), DR game day, IdP integration, retention schedule, and **HITL queue staffing** are
  customer-owned engagement work.

## Shared-responsibility (RACI) — AWS · Delivery Partner (SI) · Healthcare Org
| Area | AWS | SI / Delivery Partner | Healthcare Org (Customer) |
|---|---|---|---|
| Authorized cloud + BAA-eligible services | **R/A** | C | I |
| AWS BAA executed | C | C | **R/A** |
| Deploy the governed accelerator (CFN/TF) | I | **R/A** | C |
| IdP federation + `custom:hpp_role` mapping | I | C | **R/A** |
| Live connector build + validation | I | **R/A** | C |
| Data classification + minimum-necessary policy | I | C | **R/A** |
| Bedrock Guardrail tuning to population | I | **R/A** | C |
| Prompt/model change control | I | **R/A** | C |
| CSV/CSA validation for intended use | I | C | **R/A** |
| Penetration test + threat-model review | I | C | **R/A** |
| HITRUST/SOC 2 evidence + authorization | C | C | **R/A** |
| HITL queue staffing + SLAs | I | C | **R/A** |
| DR (RPO/RTO) ratification + game day | I | C | **R/A** |
| Day-2 operations + monitoring | I | C | **R/A** |
| Clinical / coverage accountability | I | I | **R/A** |

## Gated go-live checklist
1. ☐ AWS BAA + SI BAA executed; no PHI before both.
2. ☐ IdP integrated; roles mapped; JWT verification enabled (`AUTH_REQUIRE_JWT=1`, JWKS configured).
3. ☐ Live connectors validated against real systems (off fixture mode).
4. ☐ Bedrock Guardrail tuned; red team re-run against customer data.
5. ☐ CSV/CSA validation executed and signed.
6. ☐ Penetration test + threat-model review complete.
7. ☐ DR game day passed; RPO/RTO ratified.
8. ☐ HITL queue staffed with SLAs; reviewer roles provisioned.
9. ☐ Monitoring/alerting wired (CloudTrail/GuardDuty/Security Hub/Config).
10. ☐ HITRUST/SOC 2 evidence package assembled from the control matrix.

## Phased path
Start with a **low-blast-radius agent** (Patient Access or Member Services — read-mostly,
identity-gated) to prove the governed pattern; **not** Utilization Management or Clinical-
Administration first. Expand agent by agent on the paved road; adopt the orchestration platform
(`care_platform/`) only when a workflow genuinely spans agents.
