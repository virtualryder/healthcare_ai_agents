# Agent 04 — Compliance Mapping: Patient Access

| Obligation | How this agent satisfies it |
|---|---|
| **HIPAA Privacy — minimum necessary** | Reads only eligibility, registration, and scheduling data needed; every call is gateway-authorized with a tool-scoped token. |
| **Identity before disclosure** | `verify_identity` gates benefits/account disclosure; an unverified request returns `VERIFY_IDENTITY` and discloses nothing. |
| **No Surprises Act — Good Faith Estimate** | Patient cost comes from the deterministic `registration.estimate_cost` tool (GFE basis + disclaimer), never the LLM. |
| **HIPAA Security — audit controls** | Every decision is recorded in the append-only, PHI-masked audit log with lineage and the approving rep. |
| **No autonomous consequential action** | `human_review_gate` is framework-enforced; `scheduling.book_appointment` and `registration.create_registration` are high-risk and require a verified rep approval. |
| **Section 1557 / health literacy** | Member-facing messages pass a 6th–8th grade plain-language pre-flight; language-access is a customer configuration. |
| **Grounded figures** | Grounding fails the member message if any copay, deductible, estimate, or plan name is not traceable to the eligibility/estimate response. |

## Customer responsibilities
CSV for the intended use; IdP mapping of `PATIENT_ACCESS_REP`; live scheduling, registration,
and payer-eligibility connector validation; Guardrail configuration; language-access program;
prompt/model change control (the registry hash-pins the member-comms prompts).
