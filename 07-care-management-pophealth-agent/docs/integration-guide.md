# Agent 07 — Integration Guide

The agent calls the MCP gateway, which calls a **connector**. Implement methods in
`platform_core/hpp_agent_platform/connectors/live.py` or point `<KIND>_BASE_URL` at a façade —
signatures match the fixtures.

| Connector kind | Real system (examples) | Methods this agent uses | Standard |
|---|---|---|---|
| `careplan` | Care-management platform / pop-health analytics | `get_care_plan`, `identify_gaps`, `update_care_plan` | vendor API; HCC/RAF |
| `ehr` | Epic / Oracle Health via FHIR + HealthLake | `get_patient_summary` | HL7 FHIR R4 / US Core |
| `consent` | Consent-management / 42 CFR Part 2 registry | `check` | — |
| `kb` | Care-management policy / guidelines | `search_policy` | — |

## Identity & roles
Map `CARE_MANAGER` to your IdP (see `platform_core/hpp_agent_platform/mcp_gateway/policy.py`).

## Swapping demo → live
`export CONNECTOR_MODE=live LLM_PROVIDER=bedrock BEDROCK_GUARDRAIL_ID=...` and set the
`*_BASE_URL`s. No node or graph changes.
