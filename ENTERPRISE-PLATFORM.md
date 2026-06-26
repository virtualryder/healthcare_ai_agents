# HPP Enterprise Platform — The Story Beneath the Agents

The agents are interchangeable workloads. The asset that makes them deployable in a HIPAA
environment is the platform: one governed control plane that carries all eight workloads.

## 1. Why a governed access layer (not just LLM calls)
An agent that *automates* a system of record — pulling a chart, submitting an appeal,
updating a case — needs an enforcement point between it and that system. Without it you
have ungoverned shadow AI touching PHI. The MCP authorization gateway is that point. It is
the single place where minimum-necessary access, the human gate, scoped tokens, and the
audit trail are enforced — in code, not policy prose.

## 2. Deny-by-default with least-privilege intersection
`permitted(tool) ⇔ tool ∈ AGENT_TOOL_GRANTS[agent] ∩ ⋃ ROLE_ENTITLEMENTS[user_roles]`.
An agent can never exceed the human on whose behalf it acts. Consequential authorities are
withheld from agents entirely: a revenue-cycle agent cannot submit a claim; a UM agent
cannot issue a determination. Those live only with human roles (`BILLER`,
`UM_MEDICAL_DIRECTOR`). This is the technical expression of the posture CMS expects for AI
in coverage decisions — AI assists, a human decides.

## 3. The human gate is framework-enforced
High-risk (write/irreversible) tools block until a verified reviewer identity is bound into
the record. In LangGraph this is `interrupt_before=["human_review_gate"]`; in the AWS-native
build it is a Step Functions `waitForTaskToken` task. Application code cannot bypass it.

## 4. PHI never leaks into logs or to external AI
The PHI masker runs at every audit/trace boundary (HIPAA Safe Harbor identifiers). With
`LLM_PROVIDER=bedrock`, inference runs in-account on HIPAA-eligible Amazon Bedrock under the
AWS BAA — no PHI egress to an external AI API.

## 5. Orchestration stance — ADR-001
**Decision:** in-process LangGraph today; an A2A hop through Amazon Bedrock AgentCore only
when a workflow genuinely spans agents. An A2A hop does **not** widen authority — the
downstream agent calls the same gateway with the same acting-user claims, so the
intersection and human gates apply identically. A runnable reference hop is in
`platform_core/hpp_agent_platform/a2a/`.

## 6. From demo to production without code changes
`EXTRACT_MODE` (demo/live), `CONNECTOR_MODE` (fixture/live), and `LLM_PROVIDER`
(anthropic/bedrock) are the only switches. Connector method signatures are identical across
modes; the gateway does not know which backend is live. The path from a no-API-key demo to
an in-VPC Bedrock + live-connector deployment is configuration, not a rewrite.
