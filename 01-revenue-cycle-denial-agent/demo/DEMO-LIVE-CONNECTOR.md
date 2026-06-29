# Agent 01 — Live-Connector Reference (no API key, no real EHR)

Proves the **live connector path** end-to-end against a bundled reference façade — real HTTP
round-trips through the governed gateway, not fixtures.

```bash
# from repo root
EXTRACT_MODE=demo python 01-revenue-cycle-denial-agent/demo/demo_live.py
# or run the façade standalone and point any client at it:
python 01-revenue-cycle-denial-agent/demo/reference_facade.py    # http://127.0.0.1:8799
```

The façade (`reference_facade.py`) answers the connector methods Agent 01 calls
(`get_claim`, `validate_claim`, `check_claim_status`, `validate_codes`, `check_medical_necessity`,
`get_clinical_docs`, `search_policy`, `submit_appeal`, `update_case`) with synthetic, non-PHI
payloads. **To go live for real:** point each `*_BASE_URL` at the customer's FHIR/X12 gateway
(Epic/Oracle Health, Change Healthcare/Availity, the payer's Da Vinci endpoint) and set
`EXTRACT_MODE=live LLM_PROVIDER=bedrock BEDROCK_GUARDRAIL_ID=...`. The agent code does not change —
the gateway and connector method signatures are identical to fixture mode.
