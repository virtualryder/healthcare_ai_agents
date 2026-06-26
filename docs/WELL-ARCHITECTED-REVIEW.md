# Well-Architected Review — HPP AI Agent Suite

This review reads the suite against the **AWS Well-Architected Framework** and the
**Generative AI Lens**, pillar by pillar. It is written at the honesty of the suite's
maturity: Demonstrated and Deployable-by-design, with production hardening (CSV/CSA, IdP
integration, live-connector validation, pen test, HITRUST) scoped as engagement work. Where
a control is the customer's to configure, that is stated.

## Operational Excellence
- **Strengths:** Infrastructure as code throughout — CloudFormation (`quickstart.yaml`
  master + network/security/data/connectors/gateway/agent-service nested stacks, all
  `cfn-lint`-clean), per-agent params, and deploy scripts (`scripts/deploy.sh`,
  `build_lambdas.sh`). The governance suite (grounding, prompt registry, evals, red team,
  fairness) runs in CI as deterministic gates. Operational runbooks exist for incident
  response, DR, HITL queue operations, and model degradation.
- **GenAI Lens:** Prompt management is operationalized via the **hash-pinned prompt
  registry** — CI fails on un-bumped drift, giving auditable prompt change control.
- **Engagement work:** wire metrics/alarms to the customer's observability stack; ratify
  SLAs and on-call.

## Security
- **Strengths:** This is the pillar the suite leads with. **Deny-by-default MCP gateway**
  with **least-privilege intersection (agent grant ∩ user entitlement)** — the agent never
  exceeds the human. **Short-lived, tool-scoped tokens.** **PHI masker** (HIPAA Safe Harbor
  identifiers; preserves NPI/ICD/CPT). **PHI-masked append-only audit** (DynamoDB deny
  Update/Delete + PITR; S3 Object Lock COMPLIANCE WORM). KMS CMK encryption. **Bedrock
  Guardrails** (PII block/anonymize, denied topics incl. unauthorized determination,
  grounding). Cognito with `custom:hpp_role`. Red-team suite (injection / PHI-exfil /
  authz-bypass). In-account Bedrock inference keeps PHI under the AWS BAA with no egress.
- **GenAI Lens:** model access is governed (LLM factory), guardrails are explicit, and
  prompt-injection is a first-class red-team target.
- **Engagement work:** IdP/role-mapping integration, pen test, HITRUST assessment.

## Reliability
- **Strengths:** Stateful components are durable and recoverable — DynamoDB PITR, S3 WORM,
  regional Multi-AZ services, Step Functions for execution state. The **human gate fails
  closed**: a missed approval or recovery event does not auto-ship a high-risk write.
  DR-RUNBOOK defines RPO/RTO and a restore procedure that re-suspends, never auto-approves,
  recovered HITL items.
- **GenAI Lens:** grounding verification provides a reliability check on model output;
  degraded connectors fail to fixture/HITL fallback rather than acting blind.
- **Engagement work:** multi-Region failover is an option, not a default — ratify in the SLA.

## Performance Efficiency
- **Strengths:** Serverless-first (Lambda, Step Functions, DynamoDB on-demand) scales to
  load without standing capacity. The gateway and connectors are stateless and horizontally
  scalable. Model choice is decoupled via the LLM factory.
- **GenAI Lens — model selection:** the LLM factory lets each agent select a fit-for-purpose
  model (latency vs. capability); deterministic tools (e.g., Good Faith Estimate) bypass the
  model entirely for speed and exactness.
- **Engagement work:** right-size model selection per workload; tune token budgets.

## Cost Optimization
- **Strengths:** Pay-per-use serverless avoids idle cost; on-demand DynamoDB and Lambda bill
  to actual traffic. Deterministic tools avoid model spend where rules suffice. Fixture mode
  enables development and demos with no live-connector or inference cost.
- **GenAI Lens:** route to right-sized models; cache and ground to reduce retries; the
  prompt registry prevents costly accidental prompt regressions.
- **Engagement work:** model-mix and caching tuning against real volume; reserved capacity
  decisions if traffic stabilizes.

## Sustainability
- **Strengths:** Serverless and on-demand consumption minimizes idle compute. Right-sized
  model selection and deterministic-tool offload reduce inference energy per task.
- **GenAI Lens:** prefer the smallest model that meets the quality bar; avoid redundant
  generation through grounding and caching.

## Generative AI Lens — cross-cutting concerns
| Concern | How the suite addresses it |
|---|---|
| **Model selection** | LLM factory; deterministic tools where rules suffice; per-agent model fit |
| **Grounding** | Grounding verification (governance) + Bedrock Guardrail grounding policy |
| **Guardrails** | Bedrock Guardrails — PII block/anonymize, denied topics, grounding |
| **Human-in-the-loop** | Framework-enforced gate (LangGraph `interrupt_before` / SFN `waitForTaskToken`); named reviewer per agent; fails closed |
| **Prompt management** | Hash-pinned prompt registry; CI fails on un-bumped drift; rollback to pinned version |
| **Risk governance** | Red team, four-fifths fairness screen, eval harness, regime→control→AWS mappings (NIST AI RMF aligned) |
