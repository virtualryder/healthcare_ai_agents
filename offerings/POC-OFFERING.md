# HPP AI Agent Suite — Proof-of-Concept Offering

> A 4–6 week, fixed-scope proof of concept that puts a governed AI agent in front of
> the customer's own people on the customer's own data shape — and produces the evidence
> needed to greenlight a pilot. Every external statistic below is source-class tagged and
> traceable to `../gtm/HPP-DECK-SOURCES.md`.

## The wedge: Agent 01 — Revenue-Cycle & Denial Management

We lead with denials because it is the cleanest CFO ROI in the building. Initial denial
rates reached ~11.8% in 2024 and are climbing, and 41% of providers now report denial
rates above 10% `[industry-research]`. U.S. hospitals spent roughly $18B in 2025 overturning
denials `[industry-research]`, yet 35–60% of denied claims are never reworked at all
`[industry-research]` — abandoned because rework is manual and labor-intensive. Agent 01
triages denials, classifies root cause, and drafts a grounded, policy-cited appeal in
seconds, attacking both the per-claim rework cost (~$57 average in 2023, $25–$181 by
complexity `[industry-research]`) and the never-reworked leakage at once. A human gate
stands between the draft and any submission; no claim is auto-filed.

A POC may alternatively lead with another suite agent (02 Prior-Authorization, 05 Utilization
Management for payers) where the customer's pain is sharpest, but Agent 01 is the default
wedge for provider engagements.

## What the POC is — and is not

The POC operates the agent in `EXTRACT_MODE=demo` / `CONNECTOR_MODE=fixture` against
de-identified or synthetic data shaped to the customer's denial mix and payer profile.
It moves the suite from *Demonstrated* to a customer-contextualized demonstration. It is
**not** a production deployment: no live EHR/clearinghouse connector validation, no computer-
system validation (CSV/CSA), no penetration test, and no PHI processing. Those belong to the
pilot and the production engagement, not to a 4–6 week POC. We say so plainly to every buyer.

## Scope

| In scope | Out of scope |
|---|---|
| One agent (default: Agent 01) configured to the customer's denial/payer mix | Live connector integration to Epic / Oracle Health / Change Healthcare / Availity |
| Demo-mode workflow on synthetic or de-identified fixtures | Any PHI processing or production data |
| Walkthrough of the governed platform controls (gateway, HITL gate, PHI masker, audit) | CSV/CSA, IdP integration, HITRUST, penetration test |
| Grounded appeal-draft generation with policy citation | Auto-submission of claims or appeals (withheld by design) |
| A fit-to-value readout mapped to the customer's volumes | Contractual outcome guarantees |

## Deliverables

1. A running, customer-contextualized agent demonstration (denial triage + grounded appeal draft).
2. A governed-platform control walkthrough showing deny-by-default authorization, the
   framework-enforced human-approval gate, short-lived tool-scoped tokens, the PHI masker
   (HIPAA Safe Harbor), and the PHI-masked append-only audit trail.
3. A populated ROI value model (see `COST-ROI-MODEL.md`) using the customer's claim volume,
   denial rate, and net-revenue-per-claim inputs.
4. A target-state architecture sketch on AWS (Amazon Bedrock + AgentCore, HealthLake,
   Step Functions HITL, append-only audit + S3 Object Lock WORM, Cognito/KMS).
5. A pilot proposal and SOW outline (see `SOW-TEMPLATE.md`) with a connector-effort estimate.

## Success criteria

The POC succeeds when (a) the agent produces grounded, policy-cited appeal drafts a denials
specialist judges usable on the customer's denial samples; (b) stakeholders confirm the
governed controls satisfy a first-pass security/privacy review; and (c) the ROI model,
populated with the customer's numbers, clears the threshold the CFO sponsor sets to fund a
pilot. Acceptance is demonstration-and-readout, not a measured production KPI — that is the
pilot's job.

## Prerequisites

- An executive sponsor (CFO / VP Revenue Cycle for Agent 01) and a denials SME for review.
- A sample of de-identified or synthetic denials with payer codes (CO-197 auth, CO-50
  necessity, CO-16 coding) representative of the customer's mix.
- Read access to relevant payer policy / medical-necessity references for grounding.
- AWS account context for the architecture sketch (a live account is not required for a demo-mode POC).

## Commercials

Fixed-fee, time-boxed. **Price band: [PLACEHOLDER — SI to set per region/market].** Scoped
to a single agent and a single business unit; additional agents or business units are a
change order.

## Exit to pilot

A successful POC converts directly to the **Pilot Offering** (`PILOT-OFFERING.md`): the same
agent advanced to *Deployable* in the customer's AWS account, with SI-managed infrastructure,
the human-in-the-loop gate live, and measured KPIs over 8–12 weeks. The POC's ROI model and
SOW outline become the pilot's baseline and statement of work.
