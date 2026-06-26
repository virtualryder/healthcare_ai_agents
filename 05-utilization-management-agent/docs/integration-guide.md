# Agent 05 — Integration Guide

The agent calls the MCP gateway, which calls a **connector**. Implement methods in
`platform_core/hpp_agent_platform/connectors/live.py` or point `<KIND>_BASE_URL` at a façade —
signatures match the fixtures.

| Connector kind | Real system (examples) | Methods this agent uses | Standard |
|---|---|---|---|
| `clinicalcriteria` | MCG, Change Healthcare InterQual | `evaluate`, `get_guideline` | vendor API |
| `coding` | Encoder; CMS LCD/NCD | `check_medical_necessity` | ICD-10, CPT/HCPCS |
| `payer` | UM platform / case system | `check_pa_status`, `draft_um_recommendation` | vendor API |
| `ehr` | Epic / Oracle Health via FHIR + HealthLake | `get_clinical_docs` | HL7 FHIR R4 / US Core |
| `kb` | Medical-policy library | `search_policy` | — |

## Identity & roles
Map `UM_NURSE` (criteria + gated recommendation) and `UM_MEDICAL_DIRECTOR` (holds the withheld
determination authority) to your IdP. See `platform_core/hpp_agent_platform/mcp_gateway/policy.py`.
No agent is granted `payer.issue_determination`.

## Swapping demo → live
`export CONNECTOR_MODE=live LLM_PROVIDER=bedrock BEDROCK_GUARDRAIL_ID=...` and set the
`*_BASE_URL`s. No node or graph changes.
