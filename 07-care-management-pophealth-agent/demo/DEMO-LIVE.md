# Agent 07 — Live Path Runbook (Bedrock + real connector)

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
## 3. Live connectors (care management, EHR/HealthLake, consent)
```bash
export CONNECTOR_MODE=live
export CAREPLAN_BASE_URL=https://caremgmt.example.org
export EHR_BASE_URL=https://ehr.health.example.org/fhir
export CONSENT_BASE_URL=https://consent.example.org
```

## Security talking points
- Care-plan updates are **gated** — a care manager signs off before the plan changes.
- **42 CFR Part 2:** a SUD record without consent never produces outreach; it escalates.
- A four-fifths **fairness screen** flags disparate risk-stratification rates for review.
- Patient outreach is held to a 6th–8th grade health-literacy bar (Section 1557).
- Grounding fails outreach/plan text that asserts a gap, goal, or score not in the record.
- Every attempt is in the append-only, PHI-masked audit trail with lineage and approver.
