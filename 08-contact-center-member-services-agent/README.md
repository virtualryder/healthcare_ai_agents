# Agent 08 — Contact Center / Member Services
### HPP AI Agent Suite · status: **Documented** (spec; build follows the Agent 01 pattern)

Answers member inquiries, checks claim status (X12 276/277) and benefits/eligibility,
logs interactions, and intakes grievances — drafting tone-matched, health-literate,
Section 1557-accessible responses. Grievance creation and interaction logging are gated
writes; the agent verifies member identity before any account-specific disclosure.

**Why it matters.** Member-services volume spikes around denials and benefits questions
(the same CO-197 denials Agent 01 works); deflecting routine inquiries with grounded,
verified answers improves member experience and frees staff. Amazon Connect is the natural
CCaaS substrate.

**Systems (via gateway):** `contactcenter` (Amazon Connect), `payer` (276/277, 270/271),
`identity`, `consent`, `kb`. **Roles:** `MEMBER_SERVICES_REP`. **Key regs:** HIPAA,
Section 1557 (language access), TCPA (outreach), CMS member-communication standards.
**Workflow:** verify member → retrieve status/benefits → draft response → literacy +
compliance check → **human gate on writes** → log/route grievance.
