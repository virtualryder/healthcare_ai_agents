# Agent 04 — AWS Deployment Guide

Same governed gateway decision in both forms.

## Container (AgentCore Runtime contract)
`agent/serve.py` implements `/invocations` + `/ping` on ARM64; the `Dockerfile` builds an image
for **AgentCore Runtime** or **ECS Fargate**.
```bash
docker build -t hpp-agent-04 -f Dockerfile ..
curl -XPOST localhost:8080/invocations -d '{"task_type":"schedule","member_ref":"MBR-30551","patient_ref":"PT-40012","service":"99214","identity_assertion":"verified-idp-token","acting_user_claims":{"sub":"u","custom:hpp_role":"PATIENT_ACCESS_REP"}}'
```

## Native (Step Functions + Lambda + human gate)
Deterministic core in Lambda; the member message drafted on Bedrock; a **Step Functions**
`waitForTaskToken` task is the access-rep gate. Deploy via the suite `infra/cloudformation/`
(`AgentId=04-patient-access`, distinct `VpcCidr`).

## AWS building blocks
**Amazon Connect** (patient-access contact flows) · **Bedrock** (+ Guardrails) for the member
message · deterministic rules for the Good Faith Estimate · **Step Functions** for the gate ·
**DynamoDB + S3 Object Lock** for the PHI-masked audit · **Cognito** for workforce identity.
