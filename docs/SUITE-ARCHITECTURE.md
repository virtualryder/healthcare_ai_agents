# HPP AI Agent Suite — Reference Architecture

The suite is a governed AI agent accelerator for healthcare providers and health plans,
built AWS-native. Its defining property is that every agent operates under a deny-by-default
authorization layer and a named human gate — an agent never exceeds the human it acts for,
and never autonomously performs a high-risk write. This document describes the six-layer
reference architecture, the AWS services behind each layer, and the request path of a
single governed tool call.

## The six layers

### 1. Channel / UX
Where humans and systems engage the agent: web/clinical UIs, the contact-center voice/chat
channel (Amazon Connect for agent 08), and member-facing surfaces. This layer enforces
accessibility and health-literacy pre-flight on patient-facing output (Section 1557 / ADA),
and carries the identity gate that must clear before any PHI is disclosed.
**AWS:** Amazon Connect, API Gateway, CloudFront, Cognito (sign-in).

### 2. Agent orchestration
The reasoning/planning runtime that decides which tools to call. Implemented portably with
LangGraph (using `interrupt_before` to suspend at human gates) or with Strands / Bedrock
AgentCore. Orchestration holds **no privilege of its own** — it must ask the gateway for
every tool action.
**AWS:** Bedrock AgentCore / Lambda / Fargate hosting the LangGraph or Strands runtime.

### 3. MCP authorization gateway
The trust boundary. Deny-by-default. Every tool call is authorized as the **least-privilege
intersection of the agent's grant and the invoking user's entitlement** — so the agent can
never exceed the human. It issues **short-lived, tool-scoped tokens**, enforces the
framework human-approval gate on high-risk writes, and withholds dangerous capabilities by
policy (notably `payer.issue_determination`, withheld from all agents).
**AWS:** the portable build of API Gateway + Cognito (`custom:hpp_role` claim) + STS for
scoped tokens — the supported pattern (used by the golden path). Bedrock AgentCore
Gateway/Identity is the managed alternative, but the shipped template is **experimental —
incomplete** (missing per-tool `ToolSchema`; see `infra/cloudformation/agentcore-gateway.yaml`).

### 4. Connector framework
Typed adapters to the systems of record — EHR, clearinghouse, payer portal, FHIR/Da Vinci
APIs, payment provider, and more (14 system kinds), each runnable in **fixture or live**
mode. Connectors are where the agent actually touches a system of record, so they sit
behind the gateway and never widen scope on their own.
**AWS:** Lambda connector functions, VPC endpoints, HealthLake (FHIR), Secrets Manager.

### 5. Governance
The assurance layer that runs in CI and at runtime: grounding verification, the hash-pinned
prompt registry (CI fails on un-bumped drift), the eval harness, the red team (injection /
PHI-exfil / authz-bypass), the four-fifths fairness screen, accessibility/health-literacy
checks, and the regime→control→AWS mappings. Bedrock Guardrails enforce PII block/anonymize,
denied topics (e.g., unauthorized determination), and grounding policy at inference time.
**AWS:** Bedrock Guardrails, CloudWatch, Security Hub, plus the in-repo governance suite.

### 6. Data / audit
The PHI-masked, append-only system of record for everything the agent did. The PHI masker
strips HIPAA Safe Harbor identifiers while preserving NPI/ICD/CPT. The audit is tamper-
evident: DynamoDB denies Update/Delete with PITR, and S3 Object Lock COMPLIANCE provides
7-year WORM. The HITL table holds pending approvals and task tokens. The LLM factory routes
to the Anthropic API or **in-account Amazon Bedrock (HIPAA-eligible, under the AWS BAA, no
PHI egress).**
**AWS:** DynamoDB (audit + HITL, PITR, KMS), S3 (Object Lock WORM), KMS CMK, Step Functions
(execution state), Amazon Bedrock (inference).

## Request path of a single governed tool call

1. **Intent.** A user (or upstream event) invokes the agent through the channel layer; the
   identity gate establishes who they are and their `hpp_role` entitlement.
2. **Plan.** Orchestration decides a tool is needed (e.g., "assemble prior-authorization").
   It holds no privilege and calls the gateway.
3. **Authorize.** The gateway evaluates **agent grant ∩ user entitlement**, deny-by-default.
   If the action is out of scope, it is denied here. If it is a high-risk write, the gateway
   suspends the flow at the human gate (LangGraph `interrupt_before` / Step Functions
   `waitForTaskToken`) and enqueues an approval in the HITL table.
4. **Human gate (if applicable).** The named reviewer (e.g., PA nurse, medical director)
   approves or rejects; the decision is written to the append-only audit.
5. **Scoped execution.** On approval, the gateway mints a **short-lived, tool-scoped token**
   and the connector executes the call against the system of record in fixture or live mode.
6. **Guardrails & grounding.** Model output passes Bedrock Guardrails (PII, denied topics,
   grounding) and grounding verification before it is returned.
7. **Audit.** Every step — request, gateway decision, token scope, approval, connector call,
   Guardrail intervention, result — is written PHI-masked to the append-only audit (WORM).
8. **Return.** The result is surfaced through the channel layer, accessibility-checked for
   patient-facing output.

The through-line: the gateway is the only place privilege is decided, the human gate is the
only place a high-risk write is authorized, and the audit is the only record that matters —
each is a single, defensible chokepoint.
