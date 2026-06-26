# Agent 06 — Compliance Mapping: Payment Integrity & Coding

| Obligation | How this agent satisfies it |
|---|---|
| **No autonomous financial action** | The agent FLAGS only. It is not granted `clearinghouse.submit_claim` or any recoupment/payment-adjustment tool. Recording a flag (`pas.update_case`) is high-risk and requires a verified reviewer approval. |
| **HIPAA Privacy — minimum necessary** | Reads only the claim, docs, and coding/coverage data needed; every call is gateway-authorized with a tool-scoped token. |
| **HIPAA Security — audit controls** | Every decision is recorded in the append-only, PHI-masked audit log with lineage and the approving reviewer; the audit notes no recoupment/submission is performed. |
| **CMS NCCI / MUE** | Edits are applied via the encoder connector; the agent reports them, it does not adjudicate them. |
| **False Claims Act / OIG** | Upcoding and unsupported-necessity findings are framed as flags for human confirmation — "a mismatch is a flag, never proof." |
| **Grounded coding findings** | Grounding fails the finding if any code, edit, or policy is not traceable to the analysis (suggested codes, NCCI/MUE result, coverage policy). |

## Customer responsibilities
CSV for the intended use; IdP mapping of `CODING_SPECIALIST` (and the human reviewer role that
acts on flags); live encoder/NCCI, patient-accounting, clearinghouse, and EHR connector
validation; Guardrail configuration; and prompt/model change control (the registry hash-pins
the coding prompts).
