# CloudFormation Quick Deploy — HPP Agent 01

One master template (`quickstart.yaml`) provisions a customer-isolated, HIPAA-defensible
agent environment. **An AWS Business Associate Agreement must be in place before processing
PHI.**

| Template | Purpose |
|---|---|
| `quickstart.yaml` | Master — nests the stacks; `GatewayMode` + `DeployMode` switch variants |
| `network.yaml` | Per-agent VPC, private subnets, NAT, **Bedrock VPC interface endpoint** (PrivateLink; no PHI egress to external AI APIs), S3 endpoint, Flow Logs |
| `security.yaml` | KMS CMK, **Bedrock Guardrail** (PHI block/anonymize + unauthorized-determination denied topic), Cognito pool+client carrying `custom:hpp_role`, least-privilege agent role |
| `data.yaml` | Append-only DynamoDB audit (PITR, KMS), HITL table, **S3 Object Lock COMPLIANCE (WORM, 7-yr default)** |
| `connectors.yaml` | One governed connector dispatcher Lambda — the only thing that talks to a system of record |
| `gateway-portable.yaml` | MCP layer **Path A** — API Gateway HTTP API + Cognito JWT authorizer (**any commercial Region, day one**) |
| `agentcore-gateway.yaml` | MCP layer **Path B** — Bedrock AgentCore Gateway + Identity (AgentCore Regions) |
| `agent-service.yaml` | The agent — native (Step Functions + `waitForTaskToken` HITL) or container (ECS Fargate / AgentCore Runtime) |

```bash
# Stage nested templates to S3, then deploy the master:
scripts/deploy.sh 01-revenue-cycle-denial dev portable native s3://my-cfn-bucket/hpp
```
or directly:
```bash
aws cloudformation deploy --template-file quickstart.yaml \
  --stack-name hpp-01-revenue-cycle-denial-dev \
  --parameter-overrides AgentId=01-revenue-cycle-denial Environment=dev \
                        GatewayMode=portable DeployMode=native \
                        TemplateBaseUrl=https://my-cfn-bucket.s3.amazonaws.com/hpp \
  --capabilities CAPABILITY_NAMED_IAM
```

### Two gateway paths, one policy (`GatewayMode`)
Both front doors route to the **same connector Lambda** and enforce the **same** deny-by-default
decision from `platform_core`. `portable` deploys anywhere day one; `agentcore` is for
AgentCore-enabled Regions. Migrating A→B changes only the gateway stack.

### Two ways to run the agent (`DeployMode`)
`native` — deterministic core in Lambda, Bedrock drafting, **Step Functions** with a
`waitForTaskToken` HITL gate (the reviewer approval resumes the machine). `container` — the
LangGraph agent unchanged on ECS Fargate / AgentCore Runtime (ARM64, `/invocations`+`/ping`).

> **PHI/HIPAA:** inference stays in-account via the Bedrock VPC endpoint; the Guardrail blocks
> SSN/bank/card and anonymizes name/address/age/email/phone; the audit table is append-only
> and KMS-encrypted; finalized snapshots land in the WORM bucket. Terraform parity is on the
> roadmap (`../terraform/`).

### Stamping out additional agents
The same template set deploys every agent — only parameters change (see `params/`). Each agent gets its own isolated VPC, KMS key, Cognito pool, audit table, WORM bucket, gateway, and state machine. Pass a distinct `VpcCidr` to co-deploy agents in one account/Region:

```bash
scripts/deploy.sh 01-revenue-cycle-denial dev portable native s3://my-cfn-bucket/hpp 10.30.0.0/16
scripts/deploy.sh 02-prior-authorization  dev portable native s3://my-cfn-bucket/hpp 10.31.0.0/16
```
