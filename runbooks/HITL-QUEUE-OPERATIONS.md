# HITL Queue Operations — HPP AI Agent Suite

The human-in-the-loop (HITL) approval queue is the control that keeps every agent under a
named human's authority. No high-risk write ships without an approval. This runbook
covers operating that queue: per-agent reviewer roles and SLAs, escalation, audit of
approvals, the mechanics of a suspended state machine, and the metrics that prove the gate
is working.

## How the gate works

High-risk writes are paused by the framework before they execute — LangGraph
`interrupt_before` in the portable runtime, or Step Functions `waitForTaskToken` in the
AWS-native runtime. The execution suspends and emits a task token; the pending item lands
in the HITL DynamoDB table. A named reviewer approves or rejects; the decision (with
reviewer identity, timestamp, and rationale) is written to the append-only audit, and the
token resumes or terminates the execution. The agent operates as agent grant ∩ user
entitlement, so a reviewer can only approve actions within their own authority.

## Reviewer roles and SLA targets by agent

| Agent | Human gate (reviewer) | What is gated | Default review SLA |
|---|---|---|---|
| 01 Revenue-Cycle & Denial | **Denials specialist** | Denial work product; the agent **cannot submit a claim** | 4 business hrs |
| 02 Prior-Authorization | **PA nurse** | PA assembly/submission; the **coverage decision remains the payer's** | 2 business hrs (timely-filing sensitive) |
| 03 Clinical-Administration | **Clinician sign-off** | Draft notes only — **no order entry**; 42 CFR Part 2 consent check before disclosure | 1 business day |
| 04 Patient Access | **Access representative** | Deterministic Good Faith Estimate; **identity gate** before disclosure | 1 business hr (member-facing) |
| 05 Utilization Management | **Medical director** | Adverse recommendation is **forwarded, never auto-denied**; `payer.issue_determination` withheld from all agents; four-fifths fairness screen | 24 hrs (urgent: 72 hr regulatory clock applies) |
| 06 Payment Integrity & Coding | **Payment-integrity reviewer** | Flags only — **no recoupment, no submit** | 2 business days |
| 07 Care Management & Population Health | **Care manager** | Risk-stratification output (fairness screen); 42 CFR Part 2 consent | 1 business day |
| 08 Contact Center / Member Services | **Member-services rep** | Member-facing responses via Amazon Connect; **identity gate** before disclosure; the agent **cannot submit an appeal** | Real-time / same shift |

SLAs are defaults — ratify per engagement against regulatory clocks (e.g., CMS-0057-F PA
turnaround, UM urgent/standard timeframes) and the customer's operational commitments.

## Escalation

- **Approaching SLA breach:** auto-escalate to the reviewer's supervisor; for clinical and
  UM gates, escalate to the Medical Director on call. Never let an item time out into an
  auto-approval — the gate fails closed, so a missed SLA means the action does **not**
  ship, and the workflow surfaces as overdue rather than silently completing.
- **Reviewer dispute / out-of-scope:** if the requested action exceeds the reviewer's
  entitlement, the gateway already denies it; route to a reviewer with the correct
  authority. Determination authority is never granted to an agent under any escalation.
- **Volume surge:** add reviewers to the role pool; do not relax the gate or raise
  per-agent autonomy.

## Audit of approvals

Every approval and rejection is an append-only audit event (PHI-masked) carrying: agent
ID, correlation/session ID, the proposed action, reviewer identity, decision, rationale,
and timestamp. Because the audit denies Update/Delete (PITR) and is WORM-protected (S3
Object Lock COMPLIANCE), the approval record is tamper-evident — this is the evidence a
HITRUST/SOC 2 assessor or a CMS reviewer reads to confirm a human decided. Periodically
sample approvals for: rationale completeness, reviewer-in-role, and SLA adherence.

## What happens to a suspended state machine (waitForTaskToken)

A suspended Step Functions execution is holding a task token and consuming no compute
while it waits. Operationally:

- **Pending:** the item is in the HITL table; the execution is parked indefinitely (no
  forced timeout that would auto-resolve). Reviewers see it in the queue.
- **Approved:** `SendTaskSuccess` with the token resumes the execution to perform the
  gated write (within the user's entitlement).
- **Rejected:** `SendTaskFailure` terminates that path; the agent records the rejection
  and does not act.
- **Lost token (after a DR event):** never auto-approve. Re-enqueue from the restored HITL
  table as a fresh, still-suspended approval for human re-review (see DR-RUNBOOK.md).

## Metrics to watch

- **Queue depth** and **age of oldest pending** per agent/role.
- **Time-to-decision** vs. SLA; **SLA-breach count** (each is an overdue, never an
  auto-approval).
- **Approval vs. rejection rate** per agent — a rising rejection rate can signal model or
  prompt drift (see MODEL-DEGRADATION-RESPONSE.md).
- **Reviewer-in-role rate** — approvals always made by a reviewer with matching entitlement.
- **Re-review count** after DR — should reconcile to zero unmatched tokens.
