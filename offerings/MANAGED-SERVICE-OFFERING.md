# HPP AI Agent Suite — Managed Service Offering

> Ongoing run-and-operate for governed AI agents deployed in the customer's AWS account.
> A deployed agent that touches PHI and gates consequential actions is not a fire-and-forget
> workload — it needs model-risk change control, a staffed human-review queue, audit review,
> and connector maintenance. This offering provides that operating discipline under SLAs.
> Statistics are source-class tagged and traced to `../gtm/HPP-DECK-SOURCES.md`.

## What we run

The SI operates one or more deployed agents (e.g., Agent 01 Revenue-Cycle, Agent 02
Prior-Authorization, Agent 05 Utilization Management) and the shared governed platform in the
customer's account: the MCP authorization gateway, the in-account Bedrock inference path with
Guardrails, the human-in-the-loop task store, the PHI-masked append-only audit trail, the
connector framework, and the governance components (grounding, prompt registry, eval harness,
fairness, accessibility). The customer owns the data and the consequential decisions; the SI
owns the reliability, security posture, and change discipline of the platform.

## Service components

**Model-risk change control.** Every change to a model version, a prompt, a guardrail, a tool
grant, or a connector is treated as a governed change. Prompts are hash-pinned in the prompt
registry; a prompt change is a versioned, reviewed event, not an edit. Before any model or
prompt change reaches production, it is run through the eval harness against golden artifacts,
the red-team suite, the grounding-verification checks, and the four-fifths fairness screen.
Nothing that fails the gates ships. This is the model-risk-management posture a CISO and a
model-risk committee expect.

**HITL queue operations.** The human-review queue is the throughput-critical surface of every
agent. We monitor queue depth, time-to-review, and reviewer SLA adherence; alert on backlog;
and report on the integrity invariant that 100% of consequential writes pass through a
verified human reviewer. The withheld authorities remain withheld — an agent never submits a
claim or issues a determination — so the queue is where human judgment is applied, and we keep
it healthy.

**Audit review.** The append-only audit trail (DynamoDB with Update/Delete denied, S3 Object
Lock WORM) is reviewed on a defined cadence for completeness and anomalies, with the PHI
masker confirmed active at every audit/trace boundary so no Safe Harbor identifier leaks into
logs. We produce periodic audit-readiness reports the customer's compliance function can use
for HIPAA Security Rule evidence.

**Connector maintenance.** Live connectors to the EHR, clearinghouse, and payer systems drift
as those systems version. We monitor connector health, manage credential rotation for
short-lived tool-scoped tokens, and remediate breakages — including FHIR-API changes driven by
CMS-0057-F as payers stand up the four required APIs ahead of Jan 1, 2027 `[gov]`.

## SLA framework (illustrative; finalized per contract)

| Dimension | Target (placeholder) |
|---|---|
| Platform availability | [PLACEHOLDER]% monthly |
| HITL queue monitoring & alerting | Continuous; backlog alert within [PLACEHOLDER] |
| Model/prompt change lead time (through eval+red-team gates) | [PLACEHOLDER] business days |
| Connector-break remediation | Sev-based; P1 within [PLACEHOLDER] |
| Security-patch / guardrail update | Within [PLACEHOLDER] of release |
| Audit-readiness reporting cadence | [PLACEHOLDER] (e.g., monthly) |

## Governance reporting

A recurring operating review covering: KPI trend for each live agent (draft acceptance,
analyst minutes saved, recovery lift); HITL queue health and gate integrity; eval/red-team/
fairness results for any change shipped; audit completeness; connector status; and a
forward look at regulatory changes (CMS-0057-F milestones, CMS AI-in-UM guidance, Section
1557, No Surprises Act) that affect the deployed agents.

## What stays with the customer

Clinical and coverage decisions, claim submissions, note signatures, and determinations stay
with the customer's licensed and credentialed staff — the agent assists, drafts, assembles,
flags, and recommends. Data ownership, the BAA, and the system-of-record stay with the
customer. The managed service operates the governed platform; it does not assume the
customer's regulatory accountability for decisions.

## Commercials

Recurring monthly or annual fee, tiered by number of live agents and connector count, plus
AWS run-cost pass-through (see `TCO-MODEL.md`). **Price band: [PLACEHOLDER — SI to set per
agent count, connectors, and SLA tier].** The per-agent operating cost falls as agents are
added because they share one governed control plane.
