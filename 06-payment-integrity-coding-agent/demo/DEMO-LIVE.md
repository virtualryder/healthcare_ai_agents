# Agent 06 — Live Path Runbook (Bedrock + real connector)

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
## 3. Live connectors (encoder/NCCI, patient accounting, clearinghouse, EHR)
```bash
export CONNECTOR_MODE=live
export CODING_BASE_URL=https://encoder.example.com
export PAS_BASE_URL=https://pas.health.example.org
export EHR_BASE_URL=https://ehr.health.example.org/fhir
```

## Security talking points
- The agent **flags**; it has no recoupment, payment-adjustment, or claim-submission tool.
- A flag **cannot be recorded** without a verified payment-integrity-reviewer approval.
- Grounding fails the finding if any code, edit, or policy is not traceable to the analysis.
- A mismatch is a flag for review, never proof of fraud — the human reviewer decides.
- Every attempt is in the append-only, PHI-masked audit trail with lineage and approver.
