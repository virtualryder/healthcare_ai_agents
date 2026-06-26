# Agent 08 — Integration Guide

The agent calls the MCP gateway, which calls a **connector**. Implement methods in
`platform_core/hpp_agent_platform/connectors/live.py` or point `<KIND>_BASE_URL` at a façade —
signatures match the fixtures.

| Connector kind | Real system (examples) | Methods this agent uses | Standard |
|---|---|---|---|
| `contactcenter` | Amazon Connect (+ Contact Lens, Lex) | `get_member`, `log_interaction`, `create_grievance` | CCaaS |
| `payer` | Claims status / eligibility service | `check_claim_status`, `check_eligibility` | X12 276/277, 270/271 |
| `identity` | IdP / member identity proofing | `verify_member` | OIDC / IAL2 |
| `consent` | Consent-management registry | `check` | — |
| `kb` | Member-facing policy / FAQ library | `search_policy` | — |

## Identity & roles
Map `MEMBER_SERVICES_REP` to your IdP (see `platform_core/hpp_agent_platform/mcp_gateway/policy.py`).
The agent has no appeal-submission grant; a `DENIALS_SPECIALIST` (Agent 01) submits appeals.

## Swapping demo → live
`export CONNECTOR_MODE=live LLM_PROVIDER=bedrock BEDROCK_GUARDRAIL_ID=...` and set the
`*_BASE_URL`s. No node or graph changes.
