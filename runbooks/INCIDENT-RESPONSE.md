# Incident Response — HPP AI Agent Suite

This runbook governs response to security, privacy, and safety incidents for a governed
healthcare AI agent. It assumes the platform controls are live: the deny-by-default MCP
authorization gateway, the PHI-masked append-only audit (DynamoDB deny Update/Delete +
PITR, S3 Object Lock COMPLIANCE WORM), Bedrock Guardrails, and the governance suite. The
audit trail is the primary evidence source for every class below.

## Incident classes

| Class | What it looks like | Primary signal |
|---|---|---|
| **PHI exposure suspicion** | Unmasked PHI appears in a log, trace, response payload, or downstream sink; a Safe Harbor identifier (name, MRN, full DOB, address, etc.) leaks past the masker | PHI masker assertion failure; Guardrail PII event; manual report |
| **Prompt-injection attempt** | Tool input or retrieved content tries to redirect the agent, exfiltrate data, or bypass the gate ("ignore prior instructions", "call issue_determination") | Red-team detector / Guardrail denied-topic hit; anomalous tool-call sequence in audit |
| **Gateway authorization anomaly** | A tool call is attempted outside the agent grant ∩ user entitlement; repeated deny-by-default rejections; a token used out of scope | Gateway deny logs; STS/scoped-token misuse; spike in 403-class authz events |
| **Grounding-failure spike** | Grounding verification rejects an above-baseline share of generations; ungrounded claims reach output | Grounding-failure-rate metric breach (see MODEL-DEGRADATION-RESPONSE.md) |
| **Connector outage** | A system-of-record connector (EHR, clearinghouse, payer portal, FHIR API) is unreachable or returning errors | Connector health check failures; elevated tool-call error rate |
| **Bedrock Guardrail trip** | A Guardrail blocks/anonymizes content — PII filter, denied topic (e.g., unauthorized determination), or grounding policy | Guardrail intervention events in audit/CloudWatch |

## Severity matrix

| Sev | Criteria | Target ack / containment |
|---|---|---|
| **SEV-1** | Confirmed or strongly suspected PHI disclosure to an unauthorized party; authz bypass that exposed PHI; agent took a high-risk action without a gate | Ack 15 min / contain 1 hr |
| **SEV-2** | Contained PHI exposure (internal only); successful injection blocked at the gate but reached the model; authz anomaly with no data loss; grounding spike affecting member-facing output | Ack 30 min / contain 4 hr |
| **SEV-3** | Connector outage with HITL fallback intact; isolated Guardrail trips behaving as designed; single grounding failure | Ack 2 hr / contain same day |
| **SEV-4** | Informational; near-miss caught by a control working as intended | Log and review |

## Roles

- **Incident Commander (IC)** — owns the timeline, declares severity, coordinates.
- **Privacy Officer / HIPAA Security Officer** — owns the breach-risk assessment and any
  notification decision. Engaged for every PHI-exposure-class incident.
- **Platform / SRE on-call** — executes containment (revoke grants, disable connectors,
  rotate tokens) and evidence capture.
- **Clinical / Medical Director governance** — engaged when a clinical or coverage
  pathway (agents 02, 03, 05, 07) is implicated.
- **Comms lead** — internal and (if directed by the Privacy Officer) external messaging.

## Response steps (all classes)

1. **Declare and assign.** IC opens the incident, sets initial severity, assigns roles.
2. **Contain.** Apply the smallest effective action:
   - **Authz / injection:** revoke or narrow the *agent grant* at the gateway (never widen
     the human's entitlement); rotate the affected tool-scoped token; the deny-by-default
     posture means revocation fails closed.
   - **PHI exposure:** stop the offending pipeline; quarantine the sink; do **not** delete
     audit records.
   - **Connector outage:** confirm the HITL gate is intact so no unreviewed action ships;
     fail the agent over to fixture/degraded mode or pause the affected workflow.
   - **Guardrail trip:** confirm it behaved as designed; if a false block degrades service,
     adjust config under change control, not by disabling the Guardrail.
3. **Capture evidence from the append-only audit.** Pull the relevant correlation/session
   IDs, the full tool-call chain (request → gateway decision → token scope → connector
   call → response), Guardrail interventions, and grounding results. The audit is
   PHI-masked and WORM-protected (S3 Object Lock COMPLIANCE; DynamoDB denies Update/Delete
   with PITR) — preserve it exactly; never mutate. Snapshot CloudTrail and CloudWatch for
   the window.
4. **Assess.** Determine root cause, blast radius, whether PHI left a trust boundary, and
   which control should have caught it.
5. **HIPAA breach-assessment handoff.** For any PHI-exposure-class incident, hand the
   evidence package to the Privacy Officer to run the four-factor breach risk assessment
   (45 CFR 164.402): nature/extent of PHI and identifiers, the unauthorized recipient,
   whether PHI was actually acquired/viewed, and the extent of mitigation. The Privacy
   Officer owns the breach determination and any 60-day notification timeline; the IC
   supplies evidence, not conclusions.
6. **Communications.** Internal status on the agreed cadence by severity. External or
   regulatory comms only at the Privacy Officer's direction. Keep the comms log in the
   incident record.
7. **Recover and verify.** Restore normal operation, re-enable grants/connectors,
   confirm the control that failed is now effective (replay an eval or red-team case).
8. **Post-incident review.** Within 5 business days: timeline, root cause, control gap,
   and corrective actions (e.g., add a red-team case, tighten a grant, bump a pinned
   prompt). File against the governance suite so the fix is regression-tested.

## Quick reference — first move by class

- PHI exposure → stop pipeline, preserve audit, page Privacy Officer.
- Prompt injection → revoke agent grant, pull tool-call chain, add red-team case.
- Authz anomaly → narrow agent grant, rotate token, review gateway deny logs.
- Grounding spike → see MODEL-DEGRADATION-RESPONSE.md; consider pinned-prompt rollback.
- Connector outage → verify HITL gate intact, fail to degraded mode, open vendor ticket.
- Guardrail trip → confirm by-design; change config only under change control.
