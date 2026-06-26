# Agent 03 — Integration Guide

The agent calls the MCP gateway, which calls a **connector**. Implement methods in
`platform_core/hpp_agent_platform/connectors/live.py` or point `<KIND>_BASE_URL` at a
REST/FHIR façade — signatures match the fixtures.

| Connector kind | Real system (examples) | Methods this agent uses | Standard |
|---|---|---|---|
| `ehr` | Epic / Oracle Health via FHIR + Amazon HealthLake; Comprehend Medical | `get_patient_summary`, `get_encounter`, `get_clinical_docs`, `draft_note` | HL7 FHIR R4 / US Core |
| `careplan` | Care-management platform | `get_care_plan` | vendor API |
| `consent` | Consent-management / 42 CFR Part 2 registry | `check` | — |
| `scheduling` | Scheduling system | `get_availability` | vendor API |
| `kb` | Clinical-policy library | `search_policy` | — |

## Identity & roles
Map `CLINICAL_STAFF` and `PROVIDER` to your IdP (see
`platform_core/hpp_agent_platform/mcp_gateway/policy.py`). The provider co-signs notes
downstream of the agent's draft.

## Swapping demo → live
`export CONNECTOR_MODE=live LLM_PROVIDER=bedrock BEDROCK_GUARDRAIL_ID=...` and set the
`*_BASE_URL`s. No node or graph changes.
