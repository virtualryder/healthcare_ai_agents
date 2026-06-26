# Agent 03 — Clinical-Administration
### HPP AI Agent Suite · status: **Documented** (spec; build follows the Agent 01 pattern)

Summarizes charts, prepares visits, coordinates referrals, handles the clinical inbox and
follow-up tasks, drafts discharge documentation, and coordinates care transitions. Every
clinical artifact is a **draft for a licensed clinician to review and sign** — the agent
holds `ehr.draft_note` (gated) but no order-entry or signing authority.

**Why it matters.** Documentation and inbox burden are leading drivers of clinician
burnout; >80% of health-system execs are prioritizing agentic AI for clinical operations
and care delivery (Deloitte, Sep 2025). 21st Century Cures information-blocking rules
require timely EHI access — summaries surface, never withhold, lawful information.

**Systems (via gateway):** `ehr` (FHIR/HealthLake, Comprehend Medical), `careplan`,
`scheduling`, `idp`, `consent`, `kb`. **Roles:** `CLINICAL_STAFF`, `PROVIDER`.
**Key regs:** HIPAA, 21st Century Cures (info-blocking), CMS E/M documentation.
**Workflow:** intake → retrieve chart → summarize/prepare → draft note/referral →
compliance check → **clinician sign-off gate** → file/route.
