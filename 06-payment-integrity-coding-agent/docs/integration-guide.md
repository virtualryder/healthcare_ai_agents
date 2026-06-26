# Agent 06 — Integration Guide

The agent calls the MCP gateway, which calls a **connector**. Implement methods in
`platform_core/hpp_agent_platform/connectors/live.py` or point `<KIND>_BASE_URL` at a façade —
signatures match the fixtures.

| Connector kind | Real system (examples) | Methods this agent uses | Standard |
|---|---|---|---|
| `coding` | 3M/Solventum, Optum encoder; CMS NCCI/MUE; LCD/NCD | `suggest_codes`, `validate_codes`, `check_medical_necessity` | ICD-10, CPT/HCPCS |
| `pas` | Patient accounting | `get_claim`, `update_case` | vendor API |
| `clearinghouse` | Change Healthcare, Availity | `validate_claim` | X12 837 |
| `ehr` | Epic / Oracle Health via FHIR + HealthLake | `get_clinical_docs` | HL7 FHIR R4 |
| `kb` | Coding/medical-policy library | `search_policy` | — |

## Identity & roles
Map `CODING_SPECIALIST` to your IdP (see `platform_core/hpp_agent_platform/mcp_gateway/policy.py`).
The agent has no claim-submission grant; only a `BILLER`/`DENIALS_MANAGER` human role submits.

## Swapping demo → live
`export CONNECTOR_MODE=live LLM_PROVIDER=bedrock BEDROCK_GUARDRAIL_ID=...` and set the
`*_BASE_URL`s. No node or graph changes.
