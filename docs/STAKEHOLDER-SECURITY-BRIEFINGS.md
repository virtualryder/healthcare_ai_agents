# Stakeholder Security Briefings — HPP AI Agent Suite

The same architecture answers a different question for each stakeholder. This document gives
a tight, security-anchored pitch per role on the buying committee — what they care about,
and the specific control that earns their confidence. Use one section per conversation.

## CFO — return without unbounded risk
The financial case is real: hospitals spend roughly **$18B/year** overturning denials out of
~$43B in billing and collections, and **35–60%** of denied claims are never resubmitted
[industry-research]. The suite goes after that rework. But the CFO's exposure isn't only
cost — it's the tail risk of an automation gone wrong. The answer: the agent **cannot submit
a claim, recoup a payment, or issue a determination on its own** — every high-risk write is
human-approved, deny-by-default, and audited. You get the efficiency without buying an
unbounded liability, and you pilot it (often with AWS funding) before committing to scale.

## CMIO — clinical safety and clinician trust
The CMIO will not put an autonomous agent near a chart. The suite is designed for that
objection: agent 03 produces **draft notes only — no order entry — with a clinician sign-off
gate** and a 42 CFR Part 2 consent check before any sensitive-record disclosure. Output is
grounded (verification + Guardrail grounding policy) so clinicians aren't handed
hallucinations. Every assist is attributable in the audit. The agent extends the clinician's
reach; it never substitutes for the clinician's judgment or signature.

## CISO / Privacy Officer — control, evidence, and breach posture
This is the suite's home turf. **Deny-by-default authorization** with **least-privilege
intersection** (agent grant ∩ user entitlement — the agent never exceeds the human),
**short-lived tool-scoped tokens**, a **PHI masker** (HIPAA Safe Harbor; preserves
NPI/ICD/CPT), and a **tamper-evident append-only audit** (DynamoDB deny Update/Delete +
PITR, S3 Object Lock COMPLIANCE WORM, KMS). **Bedrock Guardrails** block/anonymize PII and
forbid unauthorized-determination topics. In-account Bedrock inference keeps PHI **under the
AWS BAA with no egress**. A red-team suite tests injection, PHI-exfil, and authz-bypass. When
the four-factor breach assessment is needed, the audit is the evidence chain.

## VP Revenue Cycle — throughput where the money leaks
With initial denial rates around **11.8% and climbing** and **41% of providers above 10%**
[industry-research], the revenue-cycle leader feels every percentage point. Agent 01 attacks
denial work product and agent 06 flags coding/payment-integrity issues — **flags only, no
recoupment, no submit.** The denials specialist and payment-integrity reviewer stay in
control via their gates, so throughput rises without surrendering accountability or creating
a compliance exposure in the chase for speed.

## VP Utilization Management — assist that stays lawful
UM is the most regulated path, and CMS is explicit that **AI may assist but a human must
decide — no algorithmic denial.** The suite enforces this in architecture, not policy text:
`payer.issue_determination` is **withheld from every agent**, an **adverse recommendation is
forwarded to the medical director, never auto-denied**, and a **four-fifths fairness screen**
runs on flag/rank steps. Agent 05's medical-director gate is non-bypassable. This is how a
plan gets UM efficiency that survives a regulator's read.

## Compliance — mapped, demonstrable, assessable
Compliance wants to see obligations mapped to controls, not promises. The suite ships a
**regime → control → AWS service → maturity** mapping covering HIPAA Privacy/Security,
HITECH, the AWS BAA, 42 CFR Part 2, CMS-0057-F, the No Surprises Act, Section 1557, Cures-Act
info-blocking, CMS AI-in-UM guidance, NIST AI RMF, HITRUST/SOC 2, and PCI. The governance
suite runs **deterministically in CI**, so controls are continuously evidenced rather than
attested once. That mapping is the spine of a HITRUST or SOC 2 evidence package.

## IRB / Clinical Governance — oversight and fairness
Clinical-governance bodies care about who is accountable, whether the system is fair, and
whether oversight is real. The suite answers with **named human gates per agent**, a
**four-fifths fairness screen** on risk-stratification and flag/rank steps (agents 05, 06,
07), **42 CFR Part 2 consent checks** (agents 03, 07), accessibility/health-literacy
pre-flight on patient-facing output (Section 1557), and an **immutable audit** that lets
governance reconstruct any decision. Oversight is built into the runtime, not bolted on as a
review meeting after the fact.
