# Deployment Models — Standalone First, Platform When Ready

The HPP suite is designed so an organization can adopt **one agent at a time**, prove it, and
only later coordinate agents across a journey. This document describes the two deployment stances
and the orthogonal infrastructure choices. References: `infra/` and the per-agent VPC CIDRs.

## Stance 1 — Standalone (start here)

**Each agent deploys its own fully isolated stack** with **no dependency on the platform and no
dependency on any other agent.** A standalone deployment provisions, for that agent alone:

- its **own VPC** (a dedicated CIDR — see the table below), private subnets, and VPC endpoints;
- its **own KMS** customer-managed CMK;
- its **own Cognito** user pool with the `custom:hpp_role` claim;
- its **own append-only audit** (DynamoDB, PITR, KMS) and **WORM** evidence bucket (S3 Object
  Lock COMPLIANCE);
- its **own MCP authorization gateway** (deny-by-default, scoped tokens, bound human gate);
- its own connectors and agent runtime.

Because nothing is shared, a standalone agent can be deployed, audited, certified, and operated
independently — and torn down without affecting anything else. This is the default and the
recommended way to land. The **canonical, acceptance-gated deploy is the Agent 01 SAM golden path**
(`infra/golden-path-01-revenue-cycle/`); the nested-CloudFormation route via `scripts/deploy.sh`
(see the per-agent handbooks in `deliverables/agent-handbooks/`) is the alternative multi-agent
reference (not acceptance-gated).

### Per-agent VPC CIDRs (give each a distinct block)
| Agent | CIDR |
|---|---|
| 01 Revenue-Cycle & Denial | `10.30.0.0/16` |
| 02 Prior-Authorization | `10.31.0.0/16` |
| 03 Clinical-Administration | `10.32.0.0/16` |
| 04 Patient Access | `10.33.0.0/16` |
| 05 Utilization Management | `10.34.0.0/16` |
| 06 Payment Integrity & Coding | `10.35.0.0/16` |
| 07 Care Management & Pop Health | `10.36.0.0/16` |
| 08 Contact Center / Member Services | `10.37.0.0/16` |

Distinct CIDRs avoid overlap if agents later peer or share transit, and keep blast radius per
agent. The CIDR is the sixth argument to `scripts/deploy.sh`.

## Stance 2 — Platform (adopt when ready)

When two or more agents are live and the customer feels the cost of the hand-offs, adopt the
**Care & Claims Orchestration Platform** — **agent by agent**. The same standalone agents become
**saga steps unchanged**. The platform does **not** require giving any agent a tool it doesn't
already hold; orchestration is purely about sequencing governed actions and compensating cleanly
when a downstream system fails (every step still authorizes through the same gateway with the same
acting-user claims). See `ENTERPRISE-PLATFORM.md` and `gtm/HPP-PLATFORM-GTM-STORY.md`.

There is no "big bang." Migration from standalone to platform is additive: a journey references
existing agent stacks; it never replaces them.

## Orthogonal choice A — IaC: CloudFormation or Terraform

Both are shipped and at parity:

| | CloudFormation | Terraform |
|---|---|---|
| Entry point | `infra/cloudformation/quickstart.yaml` (nests network/security/data/connectors/gateway/agent-service) | `infra/terraform/main.tf` + `modules/` |
| Per-agent params | `infra/cloudformation/params/<agent>.json` | `infra/terraform/envs/<agent>.tfvars` |
| Command | `scripts/deploy.sh <agent> <env> <gw> <deploy> s3://bucket/prefix <cidr>` | `terraform apply -var-file=envs/<agent>.tfvars` |

Pick the one your platform team already operates. The control semantics are identical.

## Orthogonal choice B — Runtime: native or container

The fourth argument to `scripts/deploy.sh` selects the agent service runtime:

- **`native`** — the agent runtime is a **Step Functions** state machine with Lambda. The human
  gate is `waitForTaskToken`; compensation is a `Catch` path. Lowest operational overhead;
  serverless scaling and backpressure. Recommended default.
- **`container`** — the agent runtime runs on **Fargate**. Choose this when the customer
  standardizes on containers, needs a long-lived process, or has libraries that don't fit Lambda.

## Orthogonal choice C — Gateway mode: portable or agentcore

The third argument selects the gateway:

- **`portable`** — API Gateway + Cognito + STS. Works in **every Region**. The default and
  the **supported** gateway (the same pattern the acceptance-gated golden path deploys).
- **`agentcore`** — Amazon Bedrock AgentCore Gateway/Identity. **EXPERIMENTAL — incomplete**:
  the template's MCP Lambda targets still lack the required per-tool `ToolSchema` (pending API
  confirmation), so it will not deploy as-is; it also requires an AgentCore-enabled Region.
  Use `portable` (see the header of `infra/cloudformation/agentcore-gateway.yaml` and the
  Aegis platform repo Run 10 for the live-validated MCP endpoint pattern).

## Summary
Start standalone, one isolated stack per agent with its own VPC/KMS/Cognito/audit/gateway. Choose
CloudFormation or Terraform, native or container, portable or agentcore (experimental) — independently. Adopt the
orchestration platform later, agent by agent, with no re-platforming and no widening of authority.
