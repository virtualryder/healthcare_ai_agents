# HPP Seller — First-Meeting Cheatsheet

## One sentence
"A governed AI-agent accelerator for providers and health plans on AWS — eight workflows on one
deny-by-default, auditable, HIPAA-defensible control plane, where a licensed human decides every
consequential action."

## Open by buyer
- **CFO / VP Revenue Cycle** → "Denials are the cleanest CFO ROI in the building." Lead Agent 01.
- **CMIO / VP Clinical Ops** → "Drafts a clinician signs — never order entry." Lead Agent 03.
- **Health-plan VP UM / Claims** → "The determination stays with your medical director; that's
  what keeps an AI-in-UM program defensible." Lead Agents 02 + 05; cite CMS-0057-F (2027).
- **CISO / Privacy Officer** → "Controls are enforced in the gateway, outside the model; inference
  stays in-account on HIPAA-eligible Bedrock under your BAA."

## Three proof points (no API key)
1. 270 automated tests pass (as of 2026-07-10), including red-team injection/PHI-exfil/authz-bypass.
1. 270 automated tests pass (as of 2026-07-10), including red-team injection/PHI-exfil/authz-bypass.
2. Withheld authorities are enforced in code: a test proves the agent can't issue a UM determination.
3. CloudFormation + Terraform, per-agent isolated VPC/KMS/audit, deployable in a new account.

## Qualifying questions
Initial denial rate & cost-to-collect? Dominant denial codes (CO-197 auth / CO-50 necessity /
CO-16 coding)? EHR (Epic / Oracle Health / MEDITECH)? Clearinghouse (Change Healthcare / Availity /
Waystar)? Payer-side: CMS-0057-F FHIR-API readiness? Who holds the consequential authority today?
AWS BAA in place; Bedrock enabled in-Region?

## Land-and-expand
Land **Agent 01** (fastest, most measurable, provider-side) → expand to **02 + 04** (front-to-back
loop) → payer-side **05 + 08**. Every new agent reuses the governed platform.

## Maturity honesty (say it)
Demonstrated + Deployable-by-design today. Production-readiness — CSV/CSA, IdP integration,
live-connector validation, penetration test, HITRUST — is the engagement, not a day-one deliverable.

Full citations: `HPP-DECK-SOURCES.md`. Run of show: `DEMO-STORYBOARD.md`.
