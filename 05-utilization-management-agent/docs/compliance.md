# Agent 05 — Compliance Mapping: Utilization Management

| Obligation | How this agent satisfies it |
|---|---|
| **CMS rules on AI in UM / MA prior auth** | `payer.issue_determination` is granted to **no agent**; the agent only recommends. A "does not meet" recommendation is forwarded for a human determination, never auto-denied. |
| **HIPAA Privacy — minimum necessary** | Reads only the clinical docs, criteria, and coverage policy needed; every call is gateway-authorized with a tool-scoped token. |
| **HIPAA Security — audit controls** | Every decision is recorded in the append-only, PHI-masked audit log with lineage and the approving medical director; the audit notes that the determination is the director's. |
| **Algorithmic fairness / Section 1557** | A four-fifths disparate-impact screen runs on any flag/rank cohort; a flagged rate becomes a `compliance_check` finding for human review. |
| **No autonomous adverse action** | `medical_director_gate` is framework-enforced; `payer.draft_um_recommendation` is high-risk and requires a verified medical-director approval. |
| **Grounded clinical reasoning** | Grounding fails the rationale if any indication, code, or guideline is not traceable to the criteria result or coverage policy. |
| **ERISA / NCQA UM standards** | Criteria application is documented and cited; the determination, timeliness, and notice remain human/operational responsibilities. |

## Customer responsibilities
CSV for the intended use; IdP mapping of `UM_NURSE` / `UM_MEDICAL_DIRECTOR`; live criteria
(MCG/InterQual), coverage, and EHR connector validation; Guardrail configuration; the formal
UM program (timeliness, notices, appeals); and prompt/model change control (the registry
hash-pins the UM prompts).
