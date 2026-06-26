# Agent 02 — Integration Guide

The agent calls the MCP gateway, which calls a **connector**. Implement the methods in
`platform_core/hpp_agent_platform/connectors/live.py` or point `<KIND>_BASE_URL` at a
REST/FHIR façade — signatures match the fixtures.

| Connector kind | Real system (examples) | Methods this agent uses | Standard |
|---|---|---|---|
| `payer` | Payer Da Vinci endpoints / UM portal | `check_pa_requirement`, `submit_pa`, `check_pa_status` | Da Vinci CRD/DTR/PAS, X12 278 |
| `clinicalcriteria` | MCG, Change Healthcare InterQual | `evaluate`, `get_guideline` | vendor API |
| `ehr` | Epic / Oracle Health via FHIR + HealthLake | `get_patient_summary`, `get_clinical_docs` | HL7 FHIR R4 / US Core |
| `coding` | Encoder; CMS LCD/NCD | `check_medical_necessity` | ICD-10, CPT/HCPCS |
| `idp` | Amazon Bedrock Data Automation | (document extraction) | — |
| `kb` | Medical-policy library | `search_policy` | — |

## Identity & roles
Map `PA_COORDINATOR` (assemble + gated submit) and `UM_MEDICAL_DIRECTOR` (holds the withheld
determination authority) to your IdP. See `platform_core/hpp_agent_platform/mcp_gateway/policy.py`.

## Swapping demo → live
`export CONNECTOR_MODE=live LLM_PROVIDER=bedrock BEDROCK_GUARDRAIL_ID=...` and set the
`*_BASE_URL`s. No node or graph changes.
