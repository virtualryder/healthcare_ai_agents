# Agent 08 — AWS Deployment Guide

Same governed gateway decision in both forms.

## Container (AgentCore Runtime contract)
`agent/serve.py` implements `/invocations` + `/ping` on ARM64; the `Dockerfile` builds an image
for **AgentCore Runtime** or **ECS Fargate**.
```bash
docker build -t hpp-agent-08 -f Dockerfile ..
curl -XPOST localhost:8080/invocations -d '{"inquiry_type":"claim_status","member_ref":"MBR-30551","claim_ref":"CLM-2026-55810","identity_assertion":"verified-idp-token","acting_user_claims":{"sub":"u","custom:hpp_role":"MEMBER_SERVICES_REP"}}'
```

## Native (Step Functions + Lambda + human gate)
Deterministic retrieval core in Lambda; the response drafted on Bedrock; a **Step Functions**
`waitForTaskToken` task is the rep review gate. Deploy via the suite `infra/cloudformation/`
(`AgentId=08-contact-center-member-services`, distinct `VpcCidr`).

## AWS building blocks
**Amazon Connect** (voice/chat, Contact Lens, Lex) is the contact-center substrate · **Bedrock**
(+ Guardrails) for the response · payer status/eligibility services · **Step Functions** for the
rep gate · **DynamoDB + S3 Object Lock** for the PHI-masked audit · **Cognito** for rep identity.
