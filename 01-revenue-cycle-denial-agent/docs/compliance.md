# Agent 01 — Compliance Mapping: Revenue-Cycle & Denial

This agent touches PHI (claims, clinical documentation) and produces payer-facing
artifacts (appeals). The controls below are enforced in the shared platform, not bolted
on. Full regime→control→AWS mapping: `../../governance/controls/control_mappings.py`.

| Obligation | How this agent satisfies it |
|---|---|
| **HIPAA Privacy — minimum necessary** (45 CFR 164.502(b)) | Every system call passes the deny-by-default gateway with a tool-scoped token; the agent reads only the claim, account, docs, and policy it needs. |
| **HIPAA Security — audit controls** (45 CFR 164.312(b)) | Every ALLOW/DENY/PENDING/ERROR is recorded in the append-only, PHI-masked audit log with lineage to the system reached and the approving reviewer. |
| **HIPAA / AWS BAA** | In `LLM_PROVIDER=bedrock`, inference runs on HIPAA-eligible Amazon Bedrock, reached from the customer VPC over AWS PrivateLink (a regional AWS service, not in-VPC hosting) — no PHI egress to an external AI API. HIPAA-eligible ≠ HIPAA-compliant; a signed AWS BAA and customer controls are required. |
| **No raw PHI in logs/traces** | The PHI masker (HIPAA Safe Harbor identifiers) runs at every audit/trace boundary; appeal text is PHI-checked in `compliance_check`. |
| **No autonomous consequential action** | `human_review_gate` is framework-enforced (LangGraph `interrupt_before`); `payer.submit_appeal` and `pas.update_case` are high-risk and require a verified reviewer. The agent is **not granted** `clearinghouse.submit_claim`. |
| **Accurate payer communication** | Grounding verification fails the appeal if any code, amount, date, or policy name is not traceable to the claim or approved coverage policy. |
| **No Surprises Act adjacency** | Patient cost estimates are produced by a separate deterministic tool (`registration.estimate_cost`, Good Faith Estimate basis), never by the LLM. |
| **CMS-0057-F readiness** | The payer connector is Da Vinci/X12-aligned (CRD/PAS/277); claim-status and PA-status reads map to the FHIR/278/277 surfaces the rule standardizes by Jan 1, 2027. |

## Customer responsibilities
Computer-system validation for the intended use; IdP role mapping (DENIALS_SPECIALIST /
DENIALS_MANAGER / BILLER) to the HR system; connector validation against live patient-
accounting, clearinghouse, payer, and EHR systems; Bedrock Guardrail configuration; and
change control for prompt/model updates (the prompt registry enforces hash-pinning).

This accelerator provides the control design. The customer operationalizes, validates,
and accepts accountability for it.
