# Agent 05 — Utilization Management / Medical Necessity (payer)
### HPP AI Agent Suite · status: **Documented** (spec; build follows the Agent 01 pattern)

Applies clinical criteria (MCG/InterQual), checks coverage (LCD/NCD), and prepares a UM
**recommendation** for a reviewer. The adverse-determination authority
(`payer.issue_determination`) is **withheld from every agent** and held only by a
`UM_MEDICAL_DIRECTOR` role — the technical expression of "AI assists, a human decides,"
which CMS requires for AI in Medicare Advantage coverage decisions. A four-fifths fairness
screen runs on any flag/rank step.

**Why it matters.** 70% of health plans are prioritizing agentic AI for utilization
management, prior authorization, and claims (Deloitte, Sep 2025); algorithmic UM is under
active regulatory and litigation scrutiny, making the withheld-determination control
central to a defensible deployment.

**Systems (via gateway):** `clinicalcriteria`, `coding` (LCD/NCD), `payer`, `ehr`, `kb`.
**Roles:** `UM_NURSE`, `UM_MEDICAL_DIRECTOR`. **Key regs:** CMS AI-in-UM guidance, ERISA,
NCQA UM standards, Mental Health Parity, Section 1557.
**Workflow:** intake → evaluate criteria → check necessity → draft recommendation →
fairness + compliance check → **medical-director determination gate**.
