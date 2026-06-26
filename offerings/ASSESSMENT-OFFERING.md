# HPP AI Agent Suite — Discovery & Readiness Assessment

> A structured 2–4 week assessment that establishes whether — and how fast — a governed AI
> agent can be deployed in the customer's environment. It produces a readiness scorecard, a
> governance gap analysis, and a prioritized agent roadmap. It is the lowest-risk front door
> to the suite and de-risks every downstream POC, pilot, and production engagement.
> Statistics are source-class tagged and traced to `../gtm/HPP-DECK-SOURCES.md`.

## Why assess first

An agent that automates a system of record needs an enforcement point between it and that
system, an IdP that carries role entitlements, in-account inference under a BAA, and live
connectors to the EHR / clearinghouse / payer systems it reads and writes. The assessment
inventories all of these before a line of pilot code is committed, so the pilot SOW is priced
against reality rather than assumptions. The market is moving: >80% of health-system execs
are prioritizing agentic AI for clinical operations, care delivery, and revenue cycle, and
70% of health plans for utilization management, prior authorization, and claims
`[industry-research]`. The differentiator is governed deployment, and that starts with
readiness.

## Assessment dimensions

**Data and systems.** EHR platform (Epic / Oracle Health / MEDITECH) and FHIR maturity;
clearinghouse (Change Healthcare / Availity / Waystar); payer systems; data shape and
quality for the target workflow; HealthLake or FHIR-store availability. These determine
connector effort across the suite's 14-system connector framework (fixture/live).

**Identity provider.** Current IdP and federation path to Cognito / AWS Identity Center;
how roles and entitlements are represented today; whether the consequential-authority roles
(`BILLER`, `UM_MEDICAL_DIRECTOR`, signing clinician) can be expressed so the gateway's
least-privilege intersection maps cleanly to real people.

**Bedrock and AWS posture.** Whether an AWS BAA is in place; whether Amazon Bedrock is
enabled in the customer's Region; account structure, networking, and KMS posture for an
isolated in-VPC, in-account inference deployment with Bedrock Guardrails.

**HIPAA / BAA and regulatory posture.** HIPAA Privacy/Security + HITECH coverage; 42 CFR
Part 2 (SUD) handling where relevant; for payers, CMS-0057-F FHIR-API readiness ahead of the
Jan 1, 2027 mandate (with operational, PA denial-reason/turnaround, and metrics provisions
due Jan 1, 2026) `[gov]`; No Surprises Act Good Faith Estimate obligations `[gov]`; Section
1557 nondiscrimination `[gov]`; and, for coverage decisions, CMS expectations for AI in
utilization management.

**Governance gap analysis.** A control-by-control read of the customer's current AI
governance against what the platform enforces: deny-by-default authorization, the
framework-enforced human gate, short-lived tool-scoped tokens, PHI masking (HIPAA Safe
Harbor), the append-only audit trail, grounding verification, the hash-pinned prompt
registry, the eval harness and red team, the four-fifths fairness screen, and
accessibility / health-literacy checks. Each is mapped regime → control → AWS service.

## Deliverables

1. A **readiness scorecard** across the five dimensions, with red/amber/green ratings and the
   specific blockers for each.
2. A **governance gap analysis** mapping the customer's current state to the platform's
   enforced controls, with remediation actions.
3. A **prioritized agent roadmap** — which agent to land first (default: Agent 01 for
   providers; Agents 02 + 05 for payers) and the expand sequence, with rationale.
4. A **connector-effort estimate** per target system, feeding the POC/pilot SOW.
5. A **target-state AWS architecture** for the first agent, with the regime→control→AWS
   service mappings.

## Buyer alignment

| Buyer | What the assessment answers |
|---|---|
| CFO / VP Revenue Cycle | Where the denial dollars and rework cost concentrate, and how fast Agent 01 can land |
| CMIO / VP Clinical Operations | Whether the clinician-sign-off model and 42 CFR Part 2 gates fit current workflow |
| Health-plan VP UM / Claims | CMS-0057-F readiness and how the withheld-determination control keeps AI-in-UM defensible |
| CISO / Privacy Officer | Whether in-account Bedrock under BAA and gateway-enforced controls clear security review |

## Commercials

Fixed-fee, 2–4 weeks. **Price band: [PLACEHOLDER — SI to set].** Frequently sold as a paid
discovery that credits toward a subsequent POC or pilot.

## Exit

The assessment exits to a **POC** (`POC-OFFERING.md`) when the customer wants to see value on
their data shape first, or directly to a **Pilot** (`PILOT-OFFERING.md`) when readiness is
green and the sponsor is funded. Either way, the scorecard and connector estimate become the
SOW's assumptions baseline.
