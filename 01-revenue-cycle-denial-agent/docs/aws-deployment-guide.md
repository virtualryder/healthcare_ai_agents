# Agent 01 — AWS Deployment Guide

Two ways to run the agent on AWS; both enforce the same governed gateway decision.

## Container (AgentCore Runtime contract)
`agent/serve.py` implements the `/invocations` + `/ping` HTTP contract on ARM64. The
`Dockerfile` builds an image that registers with **Amazon Bedrock AgentCore Runtime**
in an AgentCore-enabled Region, or runs on **ECS Fargate** anywhere.

```bash
docker build -t hpp-agent-01 -f Dockerfile ..
docker run -p 8080:8080 -e EXTRACT_MODE=demo hpp-agent-01
curl localhost:8080/ping
curl -XPOST localhost:8080/invocations -d '{"claim_ref":"CLM-2026-55810","acting_user_claims":{"sub":"u","custom:hpp_role":"DENIALS_SPECIALIST"}}'
```

## Native (Step Functions + Lambda + human gate)
The deterministic core runs in Lambda; Bedrock drafts the appeal; a **Step Functions**
state machine orchestrates the flow with a `waitForTaskToken` task at the human gate —
the denials-specialist approval resumes the machine. The state machine *is* the agent.
See the suite-level `infra/cloudformation/` and `aws-native-reference/` (built out across
the suite roll-out).

## AWS building blocks for this agent
- **Amazon Bedrock** (HIPAA-eligible, in-account) — appeal drafting; **Guardrails** for PHI/topic filters.
- **Amazon HealthLake** — FHIR store for the EHR connector (`ehr.get_clinical_docs`).
- **Amazon Bedrock Data Automation** — document extraction for clinical attachments.
- **Step Functions** — approval orchestration (`waitForTaskToken`).
- **DynamoDB (append-only) + S3 Object Lock** — tamper-evident, PHI-masked audit.
- **Cognito / Identity Center** — federated workforce identity feeding the gateway.

## Pre-flight
Bedrock model access in-Region; an AWS BAA in place; KMS CMKs; the Guardrail provisioned
(`BEDROCK_GUARDRAIL_ID`); IdP role mapping. Production-readiness (CSV/CSA, live connector
validation, penetration test) is the engagement, not a day-one deliverable.
