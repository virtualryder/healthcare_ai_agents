# Agent 06 — AWS Deployment Guide

Same governed gateway decision in both forms.

## Container (AgentCore Runtime contract)
`agent/serve.py` implements `/invocations` + `/ping` on ARM64; the `Dockerfile` builds an image
for **AgentCore Runtime** or **ECS Fargate**.
```bash
docker build -t hpp-agent-06 -f Dockerfile ..
curl -XPOST localhost:8080/invocations -d '{"claim_ref":"CLM-2026-55810","encounter_ref":"ENC-88231","billed_cpt":["99215"],"billed_icd10":["E11.9"],"acting_user_claims":{"sub":"u","custom:hpp_role":"CODING_SPECIALIST"}}'
```

## Native (Step Functions + Lambda + human gate)
Deterministic edit/comparison core in Lambda; the finding drafted on Bedrock; a **Step
Functions** `waitForTaskToken` task is the reviewer gate. Deploy via the suite
`infra/cloudformation/` (`AgentId=06-payment-integrity-coding`, distinct `VpcCidr`).

## AWS building blocks
**Bedrock** (+ Guardrails) for the finding · **HealthLake** for the EHR connector · deterministic
NCCI/MUE and necessity rules · **Step Functions** for the reviewer gate · **DynamoDB + S3 Object
Lock** for the PHI-masked audit · **Cognito** for coding-workforce identity.
