# Agent 05 — Live Path Runbook (Bedrock + real connector)

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
## 3. Live connectors (MCG/InterQual, coverage, payer, EHR)
```bash
export CONNECTOR_MODE=live
export CLINICALCRITERIA_BASE_URL=https://criteria.example.com
export PAYER_BASE_URL=https://payer.example.com/fhir
export EHR_BASE_URL=https://ehr.health.example.org/fhir
```

## Security talking points
- The agent **cannot issue a coverage determination** — `payer.issue_determination` is
  granted to **no agent**. Even an adverse recommendation is forwarded for a human decision.
- A recommendation **cannot be recorded** without a verified medical-director approval.
- A four-fifths **fairness screen** flags disparate selection rates for human review.
- Grounding fails the rationale if any indication, code, or guideline is not traceable to the
  criteria result or coverage policy.
- Every attempt is in the append-only, PHI-masked audit trail with lineage and approver.
