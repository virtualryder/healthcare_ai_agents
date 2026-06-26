# Agent 08 — Live Path Runbook (Bedrock + Amazon Connect)

Runs end-to-end with **no API key** (fixtures); flips to live by configuration.

## 1. Deterministic (default)
```bash
export EXTRACT_MODE=demo && python demo/demo_run.py
```
## 2. Live Bedrock (in-account, under AWS BAA)
```bash
export EXTRACT_MODE=live LLM_PROVIDER=bedrock BEDROCK_REGION=us-east-1 BEDROCK_GUARDRAIL_ID=<id>
python demo/demo_run.py
```
## 3. Live connectors (Amazon Connect, payer status/eligibility)
```bash
export CONNECTOR_MODE=live
export CONTACTCENTER_BASE_URL=https://connect.example.org
export PAYER_BASE_URL=https://payer.example.com/fhir
```

## Security talking points
- **Identity first:** no account/benefit/claim detail is disclosed without a verified member.
- **Writes are gated:** logging an interaction and filing a grievance require a verified rep approval.
- The agent **cannot submit an appeal** (`payer.submit_appeal` not granted) — it hands off to revenue cycle.
- Member responses are held to a 6th–8th grade health-literacy bar (Section 1557 / language access).
- Grounding fails any response that states a claim status, benefit, or amount not in the record.
- Every attempt is in the append-only, PHI-masked audit trail with lineage and approver.
