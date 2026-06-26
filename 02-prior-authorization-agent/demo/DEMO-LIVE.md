# Agent 02 — Live Path Runbook (Bedrock + real connector)

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

## 3. Live connectors (Da Vinci PAS/CRD/DTR, criteria, EHR)
```bash
export CONNECTOR_MODE=live
export PAYER_BASE_URL=https://payer.example.com/fhir
export CLINICALCRITERIA_BASE_URL=https://criteria.example.com
export EHR_BASE_URL=https://ehr.health.example.org/fhir
```
Each call becomes a REST/FHIR round-trip through the gateway's scoped token. Signatures match
the fixtures — no agent code changes.

## Security talking points
- The agent **cannot issue a coverage determination** (`payer.issue_determination` is granted
  to no agent — only a `UM_MEDICAL_DIRECTOR` role).
- A PA request **cannot be submitted** without a verified PA-nurse approval.
- Grounding fails the rationale if any code/indication/guideline is not traceable to the record.
- Every attempt is in the append-only, PHI-masked audit trail with lineage and approver.
