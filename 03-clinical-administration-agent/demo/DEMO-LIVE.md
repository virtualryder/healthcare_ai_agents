# Agent 03 — Live Path Runbook (Bedrock + real connector)

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
## 3. Live connectors (EHR FHIR/HealthLake, care mgmt, consent)
```bash
export CONNECTOR_MODE=live
export EHR_BASE_URL=https://ehr.health.example.org/fhir
export CAREPLAN_BASE_URL=https://caremgmt.example.org
export CONSENT_BASE_URL=https://consent.example.org
```

## Security talking points
- The agent **drafts; a clinician signs.** `ehr.draft_note` is a gated draft write; the agent
  has no order-entry or signing authority.
- **42 CFR Part 2:** a SUD record without consent never produces an artifact — it escalates.
- Grounding fails any summary/note that asserts a problem, med, or result not in the chart.
- Patient-facing text (discharge, inbox) is held to a 6th–8th grade health-literacy bar.
- Every attempt is in the append-only, PHI-masked audit trail with lineage and the signer.
