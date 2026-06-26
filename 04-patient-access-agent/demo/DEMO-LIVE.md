# Agent 04 — Live Path Runbook (Bedrock + real connector)

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
## 3. Live connectors (scheduling, registration, payer eligibility)
```bash
export CONNECTOR_MODE=live
export SCHEDULING_BASE_URL=https://sched.health.example.org
export REGISTRATION_BASE_URL=https://reg.health.example.org
export PAYER_BASE_URL=https://payer.example.com/fhir
```

## Security talking points
- **Identity first:** no account/benefit detail is disclosed without a verified identity.
- **Cost is deterministic:** the Good Faith Estimate comes from a rules tool, never the LLM.
- **Writes are gated:** booking and registration require a verified access-rep approval.
- Member-facing text is held to a 6th–8th grade health-literacy bar (Section 1557).
- Every attempt is in the append-only, PHI-masked audit trail with lineage and approver.
