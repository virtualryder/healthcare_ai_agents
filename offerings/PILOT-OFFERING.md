# HPP AI Agent Suite — Pilot Offering

> An 8–12 week pilot that advances one agent to *Deployable* inside the customer's own AWS
> account, with SI-managed infrastructure, the human-in-the-loop gate live, and measured
> KPIs. The pilot is where the suite crosses from a contextualized demonstration to a
> governed workload running in the customer's environment. Statistics are source-class
> tagged and traced to `../gtm/HPP-DECK-SOURCES.md`.

## Objective

Take the agent validated in the POC (default: Agent 01 — Revenue-Cycle & Denial) and stand
it up in the customer's AWS account as a deployable workload: in-account inference on
HIPAA-eligible Amazon Bedrock under the customer's AWS BAA (no PHI egress to an external AI
API), the framework-enforced human-approval gate operating live against real reviewer
identities, and a PHI-masked append-only audit trail capturing every consequential step. The
pilot produces measured KPIs the executive sponsor can take to an investment committee.

## What "Deployable" means here

The agent runs against the customer's environment using the suite's configuration switches —
`EXTRACT_MODE`, `CONNECTOR_MODE`, `LLM_PROVIDER` — moving from fixtures toward live data
without a rewrite. The container contract (ARM64, `/invocations`, `/ping`) deploys on
Step Functions (native, with `waitForTaskToken` for the HITL gate) or as a container on
ECS Fargate / AgentCore Runtime. Connector validation against live systems is scoped per the
Assessment findings and is the principal variable in pilot effort. A pilot is **not** full
production: customer computer-system validation (CSV/CSA), HITRUST certification, and a
penetration test remain part of the downstream production engagement. We state this in the SOW.

## Infrastructure (SI-managed, in customer account)

The SI deploys and operates the per-agent stack from the suite's CloudFormation (cfn-lint
clean) or Terraform parity: an isolated VPC with an in-account Bedrock endpoint and Flow
Logs; KMS plus a Bedrock Guardrail with PHI filters; Cognito (with an `hpp_role` claim) or
Identity Center federation to the customer IdP; the append-only audit store (DynamoDB with
Update/Delete denied) and S3 Object Lock WORM for the immutable record; the HITL task store;
the connector Lambdas; and the MCP authorization gateway (portable API Gateway + Cognito JWT,
or AgentCore Gateway/Identity). The deny-by-default least-privilege intersection
(`tool ∈ AGENT_TOOL_GRANTS[agent] ∩ ROLE_ENTITLEMENTS[user_roles]`) and short-lived
tool-scoped tokens are enforced in the gateway, outside the model.

## The human gate is live

In the pilot the human-approval gate is exercised by real credentialed reviewers, not
fixtures. High-risk write tools block until a verified reviewer identity is bound into the
record (LangGraph `interrupt_before` or Step Functions `waitForTaskToken`). The consequential
authorities stay withheld from the agent: Agent 01 cannot submit a claim (a `BILLER` does);
a UM pilot's agent cannot issue a determination (only a `UM_MEDICAL_DIRECTOR` holds it). The
agent assists, drafts, and recommends; a licensed or credentialed human decides.

## Measured KPIs

| KPI | What it measures |
|---|---|
| Draft acceptance rate | Share of agent-drafted appeals a specialist accepts with minor or no edits |
| Analyst minutes saved per denial | Reduction in manual rework time per worked claim |
| Throughput on previously-abandoned denials | Newly-worked share of the 35–60% historically never reworked `[industry-research]` |
| Overturn / recovery lift | Recovered net revenue on newly-worked or better-grounded appeals |
| Gate integrity | 100% of consequential writes pass through a verified human reviewer |
| Audit completeness | Every step captured in the PHI-masked append-only trail |

KPIs are baselined against the customer's pre-pilot denial metrics. The denials problem is
large enough that even modest lifts matter: of the ~$18B U.S. hospitals spent overturning
denials in 2025, much was rework cost the agent compresses `[industry-research]`.

## Prerequisites

- A completed Assessment (`ASSESSMENT-OFFERING.md`) or equivalent: AWS BAA in place, Bedrock
  enabled in-Region, IdP integration path identified, target connectors and data flows mapped.
- A named reviewer pool (denials specialists / billers for Agent 01) to exercise the HITL gate.
- A de-identified-to-limited dataset agreement and the customer's data-governance sign-off.
- An executive sponsor and a measurable baseline for the chosen KPIs.

## Commercials

Time-and-materials or fixed-fee with a connector-effort line item. **Price band:
[PLACEHOLDER — SI to set per scope and connector complexity].** Pilot scope is a single
agent and a single business unit; the per-agent marginal compliance cost falls for each
subsequent agent because the governed platform is already in place.

## Exit

A successful pilot exits to a **production engagement** (CSV/CSA, live-connector validation
across the customer's EHR/clearinghouse/payer systems, penetration test, HITRUST roadmap) and
to **land-and-expand**: a second agent (e.g., 02 Prior-Authorization or 04 Patient Access
to close the front-to-back-office loop) inheriting the same governed platform, plus the
ongoing **Managed Service** (`MANAGED-SERVICE-OFFERING.md`) to run and operate the workload.
