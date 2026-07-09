# Assurance Packet — HPP Agent 01 (Revenue-Cycle Denials & Appeals)

*One document, everything a director of architecture, a CISO, a HIPAA privacy/security officer, or a
TPRM reviewer needs to evaluate this hero agent. Every claim links to code, a test, or deployment
evidence. Boundaries: [`NOT-CLAIMS.md`](../NOT-CLAIMS.md); machine-readable status:
[`MATURITY.yaml`](../MATURITY.yaml).*

> **What this is:** a governed reference accelerator agent, **not** an AWS service, not a compliance
> certification, not HITRUST/SOC 2-certified. HIPAA-eligible AWS services under a signed BAA and
> customer controls are required — **HIPAA-eligible ≠ HIPAA-compliant.** Reference accelerator for
> discovery, architecture workshops, and scoped pilots.

> **Lead only with this agent.** Agent 01 is the **only** HPP agent with clean-account acceptance
> evidence; Agents 02–08 share the templates but are **not** individually clean-account-gated
> ([`MATURITY.yaml`](../MATURITY.yaml)).

---

## 1. At a glance

| | |
|---|---|
| **Agent** | 01 — Revenue-Cycle Denials & Appeals (read a denied claim → validate codes / medical necessity → retrieve coverage policy → draft an appeal → **human denials-specialist review** → submit appeal) |
| **Maturity** | **Deploy-validated** (clean-account acceptance — the only gated HPP agent) |
| **Governance pattern** | Conforms to **Aegis Governance Pattern (AGP) v1.0** |
| **System of record** | Documented **X12 835 / HealthLake** scaffold — **tier-1 fixture + scaffold** (no clean public denial API). Payer/clearinghouse 835 feed, Epic/ADT = **tier-4, not done** (engagement, under BAA) |
| **Data class** | **PHI (HIPAA)** — masked before any model/audit write; requires a signed AWS BAA for a real deployment |
| **Negative controls** | `make neg-demo` — **10/10 refusals enforced** (CI-gated) |

## 2. Architecture & diagrams

- **Suite / per-agent architecture:** [`docs/SUITE-ARCHITECTURE.md`](../docs/SUITE-ARCHITECTURE.md), per-agent [`docs/aws-deployment-guide.md`](docs/aws-deployment-guide.md).
- **PHI data flow:** `docs/diagrams/phi-data-flow.svg`.
- **Trust boundaries (summary):**

```
  ┌──────────── Customer AWS account (per-agent VPC, under BAA) ─────────────┐
  │  IdP/Cognito ─(verified JWT)→ [MCP AUTHORIZATION GATEWAY] ──┐           │
  │    deny-by-default · least-privilege intersection ·        │           │
  │    scoped short-lived token · fail-closed PHI mask ·       ▼           │
  │    append-only + S3 Object-Lock audit · token budget  [connector]      │
  │  Bedrock + Guardrails ◄─ PrivateLink (regional AWS)   (fixture / 835 scaffold)
  └──────────────────────┬───────────────────────────────────┘
   no PHI egress to      │ human denials specialist approves the appeal submit
   external AI APIs      ▼
        payer / clearinghouse 835 feed (tier-4, NOT here) — engagement under BAA
```

The consequential **claim submission** (`clearinghouse.submit_claim`) is **withheld from the agent** —
only a `DENIALS_MANAGER`/`BILLER` role holds it. Full trust-boundary + abuse cases:
[`docs/THREAT-MODEL.md`](../docs/THREAT-MODEL.md).

## 3. MCP / tool authorization

Deny-by-default gateway: verified identity → **least-privilege intersection** → human approval for the
appeal write → short-lived scoped token → fail-closed PHI mask → append-only audit. The agent may draft
and submit an **appeal** but cannot **submit a claim** (a biller's act). Reference logic:
[`../platform_core/hpp_agent_platform/mcp_gateway/`](../platform_core/hpp_agent_platform/mcp_gateway/)
and [`../platform_core/hpp_agent_platform/approvals.py`](../platform_core/hpp_agent_platform/approvals.py).

## 4. Control matrix (condensed)

| Control | Mechanism (code) | Evidence / test | Owner |
|---|---|---|---|
| Identity / authN | Verified IdP JWT (RS* allow-list; `none`/HS rejected) (`jwt_verify.py`) | negative demo #1–2 | Repo (federated IdP = Customer) |
| Deny-by-default authz | Least-privilege intersection (`mcp_gateway/policy.py`) | negative demo #3–4 | Repo |
| Consequential act withheld | `clearinghouse.submit_claim` / `payer.issue_determination` absent from agent grants | `policy.py` NOTEs + tests | Repo |
| Human approval (SoD) | Bound, single-use, args-bound tokens + JtiStore (`approvals.py`) | negative demo #5–7 | Repo |
| Scoped short-lived tokens | Per-call, tool-scoped, ephemeral (`mcp_gateway/tokens.py`) | gateway tests | Repo |
| Fail-closed PHI masking | Mask before any model/audit write (`phi.py`, `audit.py`) | negative demo #8 | Repo (runtime verify = Customer) |
| Append-only + WORM audit | DynamoDB append-only + S3 Object Lock | negative demo #9; clean-account run | Repo (retention config = Customer) |
| Token budget / cost control | Hard-cap preflight before spend (`budget.py`) | `test_budget.py`, negative demo #10 | Repo |
| Private-connectivity inference | Bedrock via PrivateLink under BAA; no PHI egress to external AI APIs | `network.yaml`; THREAT-MODEL | Repo/Customer |

Full mappings: [`docs/NIST-800-53-CONTROL-MATRIX.md`](../docs/NIST-800-53-CONTROL-MATRIX.md) ·
[`docs/compliance.md`](docs/compliance.md).

## 5. Deployment evidence

Agent 01's golden path was deployed to a **clean AWS account**, exercised, and torn down. Proof:
[`evidence/CLEAN-ACCOUNT-ACCEPTANCE.md`](../evidence/CLEAN-ACCOUNT-ACCEPTANCE.md). **Agents 02–08 are
NOT individually clean-account-gated** — do not present them as deploy-validated.

## 6. Negative-test results

`make neg-demo` (or run [`demo/negative_demo.py`](demo/negative_demo.py)), CI-gated by
[`../governance/tests/test_negative_demo.py`](../governance/tests/test_negative_demo.py). Latest: **10/10 enforced**.

| # | Attempt | Result |
|---|---|---|
| 1 | No / missing JWT | **DENY** — no authenticated subject |
| 2 | Bad JWT | **DENY** — malformed / disallowed alg |
| 3 | Wrong role (not entitled) | **DENY** — agent may not exceed the human |
| 4 | Unregistered tool | **DENY** — unknown tool |
| 5 | Self-approval | **DENY** — separation of duties |
| 6 | Approval replay | **DENY** — single-use jti consumed |
| 7 | Tampered args | **DENY** — binding-hash mismatch |
| 8 | Masker unavailable | **FAIL-CLOSED** — no unmasked PHI persisted |
| 9 | Audit sink unavailable | **FAIL-CLOSED** — no silent success |
| 10 | Over-budget call | **DENY** — hard cap, before spend |

## 7. Known limitations (read before a pilot)

- **Connector is a documented X12 835 / HealthLake scaffold (tier-1)** — there is no clean public denial
  API. A production payer/clearinghouse 835 feed or Epic/ADT integration is **tier-4** engagement work under a BAA.
- **PHI masking is unit-tested, not runtime-verified on AWS.** HIPAA-eligible ≠ HIPAA-compliant; the
  customer owns the BAA, configuration, and controls.
- **Only Agent 01 is clean-account-gated.** 02–08 are demonstrated, not deploy-validated.
- Not HITRUST/SOC 2-certified; federated IdP login not proven end-to-end.

## 8. Shared-responsibility RACI (condensed)

| Area | Repo (accelerator) | Customer (engagement) |
|---|---|---|
| Governed control plane (authz, approval, tokens, audit, PHI masking, budget) | **Owns** (code + tests) | Configures, operates, validates |
| IdP + entitlement source of truth | Enables | **Owns** |
| Production connectors (835 feed, Epic/ADT, HealthLake PHI) + **BAA** | Reference only | **Owns** |
| HITRUST/SOC 2, pen test, monitoring, DR | — | **Owns** |
| KMS keys, WORM retention, secrets | Reference config | **Owns** |

Full matrix: [`docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`](../docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md) ·
TPRM: [`offerings/TPRM-DUE-DILIGENCE-PACKET.md`](../offerings/TPRM-DUE-DILIGENCE-PACKET.md).

---

*If any statement here reads as stronger than [`NOT-CLAIMS.md`](../NOT-CLAIMS.md) or
[`MATURITY.yaml`](../MATURITY.yaml), those files govern.*
