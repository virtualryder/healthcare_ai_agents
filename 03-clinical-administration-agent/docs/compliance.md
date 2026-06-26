# Agent 03 — Compliance Mapping: Clinical-Administration

| Obligation | How this agent satisfies it |
|---|---|
| **HIPAA Privacy — minimum necessary** | Reads only the summary, encounter, docs, and care plan needed; every call is gateway-authorized with a tool-scoped token. |
| **HIPAA Security — audit controls** | Every decision is recorded in the append-only, PHI-masked audit log with lineage and the signing clinician. |
| **42 CFR Part 2 (SUD)** | `check_consent` runs before any artifact is produced; a Part 2 record without consent escalates and nothing is drafted or disclosed. |
| **21st Century Cures (info-blocking)** | The agent surfaces and summarizes lawful EHI — it does not withhold or interfere with access. |
| **No autonomous clinical action** | `clinician_review_gate` is framework-enforced (LangGraph `interrupt_before`); `ehr.draft_note` is a gated **draft** only. The agent holds no order-entry or signing tool. |
| **Grounded clinical content** | Grounding fails any summary/note asserting a problem, medication, result, or date not present in the chart. |
| **Section 1557 / health literacy** | Patient-facing artifacts (discharge, inbox) pass a 6th–8th grade plain-language pre-flight. |

## Customer responsibilities
CSV for the intended use; IdP mapping of `CLINICAL_STAFF` / `PROVIDER`; live EHR/FHIR, care-
management, and consent connector validation; Guardrail configuration; prompt/model change
control (the prompt registry hash-pins the summary and patient-comms prompts).
