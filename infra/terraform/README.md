# Terraform Parity — HPP Agent Suite

Equivalent IaC to `../cloudformation/` for customers whose platform engineering teams
standardize on Terraform. Identical resource topology; different surface syntax. Each agent
deploys its own isolated VPC, KMS key, Cognito pool, audit/HITL tables, WORM bucket, gateway,
and state machine. **An AWS Business Associate Agreement must be in place before processing PHI.**

## Layout
```
infra/terraform/
├── main.tf · variables.tf        # root: provider + module wiring
├── modules/
│   ├── network/                  # VPC, private subnets, NAT, Bedrock + S3 endpoints, Flow Logs
│   ├── security/                 # KMS CMK, Bedrock Guardrail (PHI), Cognito (custom:hpp_role), agent role
│   ├── data/                     # append-only audit (PITR) + HITL DynamoDB, WORM S3 Object Lock
│   ├── connectors/               # governed connector dispatcher Lambda
│   ├── gateway/                  # portable MCP gateway (API Gateway + Cognito JWT)
│   └── agent-service/            # native Step Functions waitForTaskToken HITL | container
└── envs/<agent>.tfvars           # per-agent agent_id + VPC CIDR (10.30.0.0/16 … 10.37.0.0/16)
```

## Deploy
```bash
cd infra/terraform
terraform init
terraform apply -var-file=envs/01-revenue-cycle-denial.tfvars
# co-deploy another agent in the same account/Region (distinct CIDR via its tfvars):
terraform workspace new 02-prior-authorization
terraform apply -var-file=envs/02-prior-authorization.tfvars
```
Use a separate Terraform workspace or state per agent so the eight isolated environments do
not share state.

## Mapping to CloudFormation
| Terraform module | CloudFormation template |
|---|---|
| `modules/network` | `network.yaml` |
| `modules/security` | `security.yaml` |
| `modules/data` | `data.yaml` |
| `modules/connectors` | `connectors.yaml` |
| `modules/gateway` | `gateway-portable.yaml` |
| `modules/agent-service` | `agent-service.yaml` |
| `envs/<agent>.tfvars` | `params/<agent>.json` |

## Gateway modes
The **portable** path (API Gateway HTTP API + Cognito JWT authorizer) is implemented here and
deploys in any commercial Region day one. The **AgentCore** gateway path (Bedrock AgentCore
Gateway + Identity) is provided in `../cloudformation/agentcore-gateway.yaml`; deploy that
variant via CloudFormation where AgentCore is standardized — both front doors route to the same
connector Lambda and enforce the same deny-by-default decision.

> Validate locally with `terraform init && terraform validate` against your provider versions.
