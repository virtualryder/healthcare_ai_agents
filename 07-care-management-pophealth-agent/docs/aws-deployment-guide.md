# Agent 07 — AWS Deployment Guide

Same governed gateway decision in both forms.

## Container (AgentCore Runtime contract)
`agent/serve.py` implements `/invocations` + `/ping` on ARM64; the `Dockerfile` builds an image
for **AgentCore Runtime** or **ECS Fargate**.
```bash
docker build -t hpp-agent-07 -f Dockerfile ..
curl -XPOST localhost:8080/invocations -d '{"patient_ref":"PT-40012","acting_user_claims":{"sub":"u","custom:hpp_role":"CARE_MANAGER"}}'
```

## Native (Step Functions + Lambda + human gate)
Deterministic gap/risk core in Lambda; outreach drafted on Bedrock; a **Step Functions**
`waitForTaskToken` task is the care-manager gate. Deploy via the suite `infra/cloudformation/`
(`AgentId=07-care-management-pophealth`, distinct `VpcCidr`).

## AWS building blocks
**HealthLake** (FHIR + population data) · **Bedrock** (+ Guardrails) for outreach · pop-health
risk analytics · **Step Functions** for the care-manager gate · **DynamoDB + S3 Object Lock** for
the PHI-masked, fairness-screened audit · **Cognito** for care-management identity.
