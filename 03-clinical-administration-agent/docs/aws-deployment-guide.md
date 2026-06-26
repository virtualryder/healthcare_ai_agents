# Agent 03 — AWS Deployment Guide

Same governed gateway decision in both forms.

## Container (AgentCore Runtime contract)
`agent/serve.py` implements `/invocations` + `/ping` on ARM64; the `Dockerfile` builds an image
for **AgentCore Runtime** or **ECS Fargate**.
```bash
docker build -t hpp-agent-03 -f Dockerfile ..
curl -XPOST localhost:8080/invocations -d '{"task_type":"chart_summary","patient_ref":"PT-40012","encounter_ref":"ENC-88231","acting_user_claims":{"sub":"u","custom:hpp_role":"CLINICAL_STAFF"}}'
```

## Native (Step Functions + Lambda + human gate)
Deterministic core in Lambda; Bedrock drafts the artifact; a **Step Functions**
`waitForTaskToken` task is the clinician sign-off gate. Deploy via the suite
`infra/cloudformation/` (`AgentId=03-clinical-administration`, distinct `VpcCidr`).

## AWS building blocks
Amazon **HealthLake** (FHIR chart) · **Comprehend Medical** (entity extraction) · **Bedrock**
(+ Guardrails) for drafting · **Bedrock Data Automation** for document handling · **Step
Functions** for the sign-off gate · **DynamoDB + S3 Object Lock** for the PHI-masked audit ·
**Cognito** for clinician identity.
