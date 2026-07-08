# HPP AI Agent Suite — Field Battlecard

> For SI sellers and SAs. Qualify fast, lead with the right agent, and frame against the
> alternatives. Every statistic is source-class tagged and traced to
> `../gtm/HPP-DECK-SOURCES.md`. Be honest about maturity: the suite is *Demonstrated +
> Deployable-by-design*; production-readiness (CSV/CSA, live connectors, pen test, HITRUST)
> is the engagement.

## The one-line thesis

**"The agents are not the product. The governed platform that makes them deployable,
auditable, and HIPAA-defensible is."** A prompt cannot disable deny-by-default authorization,
the human gate, PHI masking, or the audit trail — they are enforced in the gateway, outside
the model.

## Qualifying questions

- What is your current initial denial rate and cost-to-collect? Which payers and denial codes
  dominate — CO-197 (auth), CO-50 (necessity), CO-16 (coding)?
- Is your EHR Epic / Oracle Health / MEDITECH? Clearinghouse Change Healthcare / Availity /
  Waystar? (Determines connector effort.)
- For payers: where are you on CMS-0057-F FHIR-API readiness for the Jan 2027 mandate?
- Who holds the consequential authority today — claim submission, UM determination, note
  signature? (Maps directly to the withheld-tool roles.)
- Is an AWS BAA in place, and is Bedrock enabled in your Region?
- Do you have an executive sponsor and a measurable baseline to pilot against?

## Discovery cheat-sheet — pain by buyer

| Signal you hear | Likely buyer | Lead agent |
|---|---|---|
| "Denials are killing our margin / staff can't keep up with rework" | CFO / VP Rev Cycle | 01 |
| "Prior auth is crushing our physicians / staff are full-time on PA" | CMIO / VP Clinical Ops | 02 (+03 for documentation) |
| "We need to be ready for CMS-0057-F / our UM is under scrutiny" | Health-plan VP UM / Claims | 02 + 05 |
| "We can't let an AI touch PHI / how do we prove control to audit?" | CISO / Privacy Officer | platform first, any agent |

## Per-buyer one-liners

- **CFO / VP Revenue Cycle:** "Denials are the cleanest CFO ROI in the building — an agent
  that triages denials and drafts grounded, policy-cited appeals attacks both rework cost and
  the 35–60% of denials never reworked `[industry-research]`, behind a human gate with a
  PHI-masked audit trail."
- **CMIO / VP Clinical Operations:** "Documentation and inbox burden drive burnout; the
  clinical-administration agent drafts summaries, referrals, and discharge docs for a
  clinician to sign — it never signs or orders."
- **Health-plan VP UM / Claims:** "70% of plans are prioritizing agentic AI for UM, prior
  auth, and claims `[industry-research]`; our UM agent prepares a criteria-based recommendation,
  but the determination stays with your medical director — the control that keeps AI-in-UM
  defensible — and we're aligned to the CMS-0057-F 2027 FHIR mandate `[gov]`."
- **CISO / Privacy Officer:** "The controls are enforced in the gateway, outside the model.
  A prompt cannot disable deny-by-default, the human gate, PHI masking, or the audit trail,
  and inference can stay in-account on HIPAA-eligible Bedrock under your BAA."

## Objection one-liners (full responses in OBJECTION-HANDLING.md)

- *"AI can't be allowed to deny care."* — Correct, and it can't: `payer.issue_determination`
  is withheld from every agent; an adverse recommendation is forwarded to a medical director,
  never auto-denied.
- *"PHI can't leave our walls."* — With `LLM_PROVIDER=bedrock`, inference runs in-account on
  HIPAA-eligible Bedrock under your BAA; the PHI masker runs at every audit/trace boundary.
- *"Hallucination is a non-starter in healthcare."* — Outputs are grounded and verified, prompts
  are hash-pinned, Guardrails filter, and a human reviews every consequential output before it acts.
- *"Who is accountable?"* — A licensed/credentialed human decides every consequential action;
  the agent assists, drafts, flags, and recommends. The withheld tools enforce that in code.
- *"Integration will cost a fortune."* — We assess connector effort up front; the 14-system
  connector framework runs fixture-then-live with identical signatures, so demo-to-live is
  configuration, not a rewrite.

## Competitive framing

- **vs. build-it-yourself:** Anyone can wire an LLM call. The expensive, slow part is the
  governance scaffolding — deny-by-default, the framework-enforced human gate, PHI masking, the
  append-only audit, grounding, prompt pinning, fairness, the regime→control→AWS mappings — built
  and tested here (185 automated tests as of 2026-07-07, no API key), reused across eight agents.
- **vs. point tools:** A single-workflow tool brings its own governance (or none). This suite
  carries one governed control plane across denials, prior auth, UM, coding, care management,
  and member services, so compliance is consistent and the marginal cost of each agent falls.
- **vs. big-EHR-vendor AI add-ons:** Native add-ons lock you to one vendor's surface and
  rarely span payer-side UM/claims or give you a portable, inspectable authorization gateway
  under your own BAA. Our gateway semantics are replicated in `platform_core/` — readable and
  testable without an AWS account — and run across your systems, not just one EHR.

## Maturity honesty (say this)

All eight agents are built to *Demonstrated + Deployable-by-design*; the platform and
governance are built and tested. Production-readiness — customer CSV/CSA, IdP integration,
live-connector validation against Epic/Oracle Health/Change Healthcare/Availity/payer systems,
penetration test, HITRUST — is the engagement, not a day-one deliverable.
