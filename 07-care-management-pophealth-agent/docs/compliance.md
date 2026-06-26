# Agent 07 — Compliance Mapping: Care Management & Population Health

| Obligation | How this agent satisfies it |
|---|---|
| **HIPAA Privacy — minimum necessary** | Reads only the summary, plan, and gap data needed; every call is gateway-authorized with a tool-scoped token. |
| **42 CFR Part 2 (SUD)** | `check_consent` runs before any outreach is drafted; a Part 2 record without consent escalates and nothing is produced or disclosed. |
| **Section 1557 / risk-model fairness** | A four-fifths disparate-impact screen runs on the risk-stratification cohort; a flagged rate becomes a `compliance_check` finding for human review. |
| **CMS risk-adjustment integrity** | Risk signals are surfaced for the care manager, not asserted as coding; the plan and any HCC capture remain human-owned. |
| **No autonomous plan change / outreach** | `care_manager_gate` is framework-enforced; `careplan.update_care_plan` is high-risk and requires a verified care-manager approval. |
| **Section 1557 / health literacy** | Patient outreach passes a 6th–8th grade plain-language pre-flight. |
| **Grounded content** | Grounding fails outreach/plan text that asserts a gap, goal, or risk score not present in the record. |

## Customer responsibilities
CSV for the intended use; IdP mapping of `CARE_MANAGER`; live care-management, EHR, and consent
connector validation; Guardrail configuration; the risk-model governance program; and
prompt/model change control (the registry hash-pins the care-management prompts).
