# Agent 04 — Integration Guide

The agent calls the MCP gateway, which calls a **connector**. Implement methods in
`platform_core/hpp_agent_platform/connectors/live.py` or point `<KIND>_BASE_URL` at a façade —
signatures match the fixtures.

| Connector kind | Real system (examples) | Methods this agent uses | Standard |
|---|---|---|---|
| `scheduling` | Epic Cadence, Oracle Health scheduling | `get_availability`, `book_appointment` | vendor API |
| `registration` | Patient registration / ADT | `get_registration`, `create_registration`, `estimate_cost` | vendor API; NSA GFE |
| `payer` | Eligibility service / clearinghouse | `check_eligibility` | X12 270/271 |
| `identity` | IdP / patient identity proofing | `verify_patient` | OIDC / IAL2 |
| `kb` | Patient-facing policy library | `search_policy` | — |

## Identity & roles
Map `PATIENT_ACCESS_REP` to your IdP (see `platform_core/hpp_agent_platform/mcp_gateway/policy.py`).

## Swapping demo → live
`export CONNECTOR_MODE=live LLM_PROVIDER=bedrock BEDROCK_GUARDRAIL_ID=...` and set the
`*_BASE_URL`s. No node or graph changes.
