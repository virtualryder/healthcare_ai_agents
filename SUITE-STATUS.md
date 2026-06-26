# HPP AI Agent Suite — Status & Changelog

## Current state (June 2026)
- **platform_core/hpp_agent_platform** — built & tested: MCP authorization gateway
  (deny-by-default + least-privilege intersection + HITL + scoped tokens + PHI-masked
  append-only audit), PHI masker (HIPAA Safe Harbor), provider-abstracted LLM factory
  (Anthropic / Bedrock + Guardrails), connector framework (14 system kinds, fixture/live),
  A2A supervisor.
- **governance** — built & tested: grounding, prompt registry + manifest, eval harness +
  golden artifacts, red team, fairness (four-fifths), accessibility + health literacy,
  control mappings.
- **Agent 01 — Revenue-Cycle & Denial** — built to reference depth: LangGraph workflow with
  framework-enforced HITL interrupt, framework-free runner, gateway-backed tools, fixtures,
  Streamlit dashboard, AgentCore `/invocations`+`/ping` serve contract, Dockerfile, demo +
  live-path runbook, four-document doc set, full test suite.
- **infra/cloudformation (Agent 01)** — built & validated: quickstart master nesting network (VPC + in-account Bedrock endpoint + Flow Logs), security (KMS + Bedrock Guardrail with PHI filters + Cognito `hpp_role` + least-privilege role), data (append-only audit + HITL + WORM Object Lock), connectors Lambda, dual MCP gateway (portable API Gateway+Cognito JWT / AgentCore), and agent-service (Step Functions waitForTaskToken HITL | Fargate). **8 templates pass cfn-lint clean.** Plus `scripts/deploy.sh` + `build_lambdas.sh`.
- **Agents 02–08** — Documented: per-agent spec README (problem, systems, roles, regs,
  workflow) and directory scaffold; build follows the Agent 01 pattern.

## Test status
`38 passed, 1 skipped` (the skip is the LangGraph graph-wiring test when langgraph is not
installed; it passes when it is). All run with **no API key**.

```
platform_core/tests   — gateway authz/HITL, PHI masking, connectors
governance            — grounding, fairness, accessibility, HITL-enforced, red team, prompt registry
01-revenue-cycle-...  — denial classification, appeal grounding, HITL submission, tool authz
```

## Roadmap (next passes)
1. Build agents 02–08 to Demonstrated depth (same scaffold).
2. `infra/cloudformation` (network, security+Guardrail, append-only audit/WORM, connector
   Lambdas, two gateway modes, agent service) + Terraform parity.
3. `aws-native-reference` (Strands + Step Functions `waitForTaskToken` rebuilds).
4. `gtm` decks (per-agent + executive overview + CISO/CMIO adoption review) from the cited
   `HPP-DECK-SOURCES.md`; `roi-calculator` workbook.
5. `offerings` (POC, pilot, SOW, battlecard, TCO/ROI, TPRM) and `runbooks`.

## Changelog
- **2026-06-25** — Initial foundation: platform_core, governance, flagship Agent 01,
  suite docs, agent 02–08 specs. 38 tests green.

- **2026-06-25** — CloudFormation infra for Agent 01 (8 templates, cfn-lint clean) + deploy scripts.
