# Agent 01 — Integration Guide

The agent never calls a vendor SDK directly. It calls the MCP gateway, which (after
authorizing) calls a **connector**. To go live, implement the connector methods in
`platform_core/hpp_agent_platform/connectors/live.py` (or point `<KIND>_BASE_URL` at a
REST/FHIR façade) — the method signatures are identical to the fixtures.

| Connector kind | Real system (examples) | Methods this agent uses | Standard |
|---|---|---|---|
| `pas` | Epic Resolute, Oracle Health, MEDITECH patient accounting | `get_claim`, `get_account`, `update_case` | vendor API |
| `clearinghouse` | Change Healthcare, Availity, Waystar | `validate_claim`, `check_claim_status` | X12 837 / 277 |
| `payer` | Payer portal / Da Vinci endpoints | `check_claim_status`, `submit_appeal` | X12 276/277, FHIR |
| `ehr` | Epic / Oracle Health via FHIR + Amazon HealthLake | `get_clinical_docs` | HL7 FHIR R4 / US Core |
| `coding` | 3M/Solventum, Optum encoder; CMS NCCI/MUE; LCD/NCD | `validate_codes`, `check_medical_necessity` | ICD-10, CPT/HCPCS |
| `kb` | Coverage-policy / medical-policy library | `search_policy` | — |

## Identity & roles
The gateway authorizes against verified IdP claims. Map your workforce roles to the
entitlements in `platform_core/hpp_agent_platform/mcp_gateway/policy.py`:
`DENIALS_SPECIALIST` (draft + appeal), `DENIALS_MANAGER` (+ claim submission, withheld
from the agent), `BILLER` (claim submission). An agent acting for a specialist can never
reach a manager-only or biller-only tool — that is the least-privilege intersection.

## Swapping demo → live
1. `pip install -e platform_core`; implement the live connectors (or set `*_BASE_URL`).
2. `export CONNECTOR_MODE=live LLM_PROVIDER=bedrock BEDROCK_GUARDRAIL_ID=...`.
3. No node or graph code changes. Re-run `pytest tests` against a staging façade.
