# Agent 05 — AWS Deployment Guide

Same governed gateway decision in both forms.

## Container (AgentCore Runtime contract)
`agent/serve.py` implements `/invocations` + `/ping` on ARM64; the `Dockerfile` builds an image
for **AgentCore Runtime** or **ECS Fargate**.
```bash
docker build -t hpp-agent-05 -f Dockerfile ..
curl -XPOST localhost:8080/invocations -d '{"service":"inpatient admission","cpt":["99223"],"diagnosis":["I50.9"],"encounter_ref":"ENC-88231","meets":true,"acting_user_claims":{"sub":"u","custom:hpp_role":"UM_NURSE"}}'
```

## Native (Step Functions + Lambda + human gate)
Deterministic criteria core in Lambda; the rationale drafted on Bedrock; a **Step Functions**
`waitForTaskToken` task is the medical-director gate. Deploy via the suite `infra/cloudformation/`
(`AgentId=05-utilization-management`, distinct `VpcCidr`).

## AWS building blocks
**Bedrock** (+ Guardrails) for the rationale · **HealthLake** for the EHR connector · deterministic
criteria/coverage rules · **Step Functions** for the director gate · **DynamoDB + S3 Object Lock**
for the PHI-masked, fairness-screened audit · **Cognito** for UM workforce identity.
