# Agent 01 — Live Path Runbook (Bedrock + real connector)

The agent runs end-to-end with **no API key** (deterministic fixtures). It flips to live
Amazon Bedrock inference and real systems by configuration — no code changes.

## 1. Deterministic (default)
```bash
export EXTRACT_MODE=demo
python demo/demo_run.py
```
Runs the full denial workflow — load claim → classify root cause → assemble evidence →
draft appeal → grounding/PHI/literacy check → human gate → submit-on-approval — over the
sample claims, against deterministic fixtures.

## 2. Live Bedrock inference (in-account, under AWS BAA)
```bash
export EXTRACT_MODE=live LLM_PROVIDER=bedrock
export BEDROCK_REGION=us-east-1 BEDROCK_GUARDRAIL_ID=<your-guardrail-id>
python demo/demo_run.py
```
PHI never leaves the customer VPC; the appeal is drafted by Claude on Bedrock with the
configured Guardrail applied.

## 3. Live system-of-record connector
```bash
export CONNECTOR_MODE=live
export PAS_BASE_URL=https://pas.health.example.org
export CLEARINGHOUSE_BASE_URL=https://clearinghouse.example.com
export PAYER_BASE_URL=https://payer.example.com/fhir
export EHR_BASE_URL=https://ehr.health.example.org/fhir
```
Each call becomes a REST/FHIR round-trip through the gateway's scoped token. Swap the
bundled reference façade for the customer's Epic/Oracle Health, Change Healthcare/Availity,
and payer endpoints. Method signatures are identical to the fixtures.

## Security talking points
- The agent **cannot** submit a claim (`clearinghouse.submit_claim` is not granted to it).
- The appeal **cannot** be submitted without a verified denials-specialist approval.
- Every attempt is in the append-only, PHI-masked audit trail with lineage and approver.
- Grounding fails the draft if any code/amount/policy is not traceable to the source.
