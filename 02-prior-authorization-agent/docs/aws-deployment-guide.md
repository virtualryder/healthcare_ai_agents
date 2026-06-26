# Agent 02 — AWS Deployment Guide

Same governed gateway decision in both forms.

## Container (AgentCore Runtime contract)
`agent/serve.py` implements `/invocations` + `/ping` on ARM64; the `Dockerfile` builds an
image for **AgentCore Runtime** or **ECS Fargate**.
```bash
docker build -t hpp-agent-02 -f Dockerfile ..
curl -XPOST localhost:8080/invocations -d '{"service":"72148","diagnosis":["M54.16"],"encounter_ref":"ENC-88231","acting_user_claims":{"sub":"u","custom:hpp_role":"PA_COORDINATOR"}}'
```

## Native (Step Functions + Lambda + human gate)
Deterministic core in Lambda; Bedrock drafts the rationale; a **Step Functions**
`waitForTaskToken` task is the PA-nurse gate. Deploy via the suite `infra/cloudformation/`
(`AgentId=02-prior-authorization`).

## AWS building blocks
Amazon **Bedrock** (+ Guardrails) for the rationale · **HealthLake** for the EHR connector ·
**Bedrock Data Automation** for attachment extraction · **Step Functions** for the approval
gate · **DynamoDB + S3 Object Lock** for the PHI-masked audit · **Cognito** for workforce
identity. The CMS-0057-F FHIR PA APIs are the natural live payer surface.
