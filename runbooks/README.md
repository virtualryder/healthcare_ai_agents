# HPP AI Agent Suite — Operational Runbooks

This directory holds the operational runbooks for running the HPP AI Agent Suite — a
governed, AWS-native agent accelerator for healthcare providers and health plans. The
suite ships eight agents (revenue-cycle & denial, prior-authorization, clinical-
administration, patient-access, utilization-management, payment-integrity & coding,
care-management & population-health, and contact-center / member-services), each with a
named human approval gate and a deny-by-default authorization model.

These runbooks assume the platform controls described in the architecture docs are in
place: the MCP authorization gateway (deny-by-default, least-privilege intersection of
agent grant and user entitlement), the framework-enforced human-in-the-loop (HITL) gate
on high-risk writes, short-lived tool-scoped tokens, the PHI-masked append-only audit
(DynamoDB with denied Update/Delete + PITR, S3 Object Lock COMPLIANCE WORM), Bedrock
Guardrails, and the governance suite (grounding verification, hash-pinned prompt
registry, eval harness, red team, four-fifths fairness screen).

## Runbook index — when to use each

| Runbook | Use it when |
|---|---|
| `INCIDENT-RESPONSE.md` | Any suspected security, privacy, or safety event: PHI exposure suspicion, a prompt-injection attempt, a gateway authorization anomaly, a grounding-failure spike, a connector outage, or a Bedrock Guardrail trip. Defines incident classes, severity, roles, evidence capture from the audit, the HIPAA breach-assessment handoff, and comms. |
| `DR-RUNBOOK.md` | An availability or data-integrity event requiring recovery: AZ/region impairment, accidental data loss, or a corrupted state machine. Defines RPO/RTO, what is stateful, the restore procedure, recovery of suspended HITL state machines, and post-restore validation. |
| `HITL-QUEUE-OPERATIONS.md` | Day-to-day operation of the human-approval queue: per-agent reviewer SLAs, escalation, audit of approvals, handling of suspended `waitForTaskToken` executions, and queue metrics. |
| `MODEL-DEGRADATION-RESPONSE.md` | Detecting and responding to model or prompt drift: prompt-registry hash-pin change control, grounding-failure-rate monitoring, eval-harness regression, fairness-screen alerts, rollback to a pinned prompt version, and model-version change control. |

## Operating principles that run through every runbook

1. **The agent never exceeds the human.** Every tool call is authorized as the
   intersection of the agent's grant and the invoking user's entitlement. When in doubt
   during an incident, revoke the agent grant — never widen the human's.
2. **High-risk writes are gated, not autonomous.** No agent submits a claim, enters an
   order, issues a coverage determination, or recoups a payment without a named human
   approval. Determination authority (`payer.issue_determination`) is withheld from all
   agents by policy.
3. **The audit is the source of truth.** It is append-only and PHI-masked. During any
   incident, the audit is your evidence chain — preserve it, never mutate it.
4. **Honesty about maturity.** The suite is Demonstrated and Deployable-by-design.
   Production hardening (CSV/CSA validation, IdP integration, live-connector validation,
   pen test, HITRUST) is engagement work and is called out where relevant.

## Escalation contacts (populate per engagement)

| Role | Owner | Channel |
|---|---|---|
| Incident Commander | _TBD_ | _TBD_ |
| Privacy Officer / HIPAA Security Officer | _TBD_ | _TBD_ |
| Platform / SRE on-call | _TBD_ | _TBD_ |
| Clinical / Medical Director governance | _TBD_ | _TBD_ |
| AWS account team / TAM | _TBD_ | _TBD_ |
