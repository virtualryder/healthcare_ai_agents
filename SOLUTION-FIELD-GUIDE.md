# HPP Solution Field Guide — SI Sales & SA Qualification

## The one-sentence pitch by buyer
- **Health-system CFO / VP Revenue Cycle** — *"Denials are the cleanest CFO ROI in the
  building: an agent that triages denials and drafts grounded, policy-cited appeals attacks
  both the rework cost and the 35–60% of denials never reworked — behind a human gate, with
  a PHI-masked audit trail."* Lead with Agent 01.
- **CMIO / VP Clinical Operations** — *"Documentation and inbox burden drive burnout; the
  clinical-administration agent drafts summaries, referrals, and discharge docs for a
  clinician to sign — it never signs or orders."* Lead with Agent 03; note 21st Century
  Cures alignment.
- **Health-plan VP UM / Claims** — *"70% of plans are prioritizing agentic AI for UM, prior
  auth, and claims. Our UM agent prepares a criteria-based recommendation; the determination
  stays with your medical director — the control that keeps an AI-in-UM deployment
  defensible."* Lead with Agents 02 + 05; note CMS-0057-F's 2027 FHIR-API mandate.
- **CISO / Privacy Officer** — *"The controls are enforced in the gateway, outside the
  model — a prompt cannot disable deny-by-default, the human gate, PHI masking, or the audit
  trail. Inference can stay in-account on HIPAA-eligible Bedrock under your BAA."*

## Qualification questions
- What is your current initial denial rate and cost-to-collect? Which payers/denial codes
  dominate (CO-197 auth? CO-50 necessity? CO-16 coding)?
- Is your EHR Epic / Oracle Health / MEDITECH? Clearinghouse Change Healthcare / Availity /
  Waystar? These determine connector effort.
- For payer prospects: where are you on CMS-0057-F FHIR-API readiness (Jan 2027)?
- Who holds the consequential authority today (claim submission, UM determination, note
  signature)? That maps directly to the withheld-tool roles.
- Is an AWS BAA in place? Is Bedrock enabled in your Region?

## Land-and-expand
Land with **Agent 01 (revenue cycle)** — fastest, most measurable ROI, provider-side. Expand
to **02 (prior auth)** and **04 (patient access)** to close the front-to-back-office loop,
then to payer-side **05 (UM)** and **08 (member services)**. Every new agent inherits the
same governed platform — the marginal compliance cost falls with each one.

## Maturity honesty
Agent 01 is Demonstrated + Deployable-by-design. Agents 02–08 are Documented. The platform
and governance are built and tested. Production-readiness (CSV/CSA, live-connector
validation, penetration test) is the engagement, not a day-one deliverable. Say so.
