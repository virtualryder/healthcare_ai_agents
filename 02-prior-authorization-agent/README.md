# Agent 02 — Prior-Authorization
### HPP AI Agent Suite · status: **Documented** (spec; build follows the Agent 01 pattern)

Gathers medical evidence, determines payer requirements, assembles the submission,
monitors status, requests missing information, and escalates urgent cases. The agent
**assembles and submits a PA request** behind a human gate (`payer.submit_pa`, high-risk),
but the **clinical determination is always the payer's** — the agent never issues one.

**Why it matters.** Physicians complete ~39 prior authorizations per week (≈13 hours);
94% say PA delays care and 78% report it causes treatment abandonment (AMA, Dec 2024).
70% of health plans are prioritizing agentic AI for UM/PA/claims, and 93% of plan execs
expect AI to ease PA (Deloitte, Sep 2025). CMS-0057-F mandates FHIR PA APIs by Jan 1, 2027.

**Systems (via gateway):** `payer` (Da Vinci CRD/DTR/PAS, X12 278), `clinicalcriteria`
(MCG/InterQual), `coding` (LCD/NCD), `ehr` (FHIR/HealthLake), `idp` (Bedrock Data Automation), `kb`.
**Roles:** `PA_COORDINATOR`. **Key regs:** CMS-0057-F, HIPAA, state PA-transparency laws.
**Workflow:** intake → determine requirement → gather evidence → evaluate criteria →
assemble packet → compliance check → **human gate** → submit/monitor → escalate-if-urgent.
