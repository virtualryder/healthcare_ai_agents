# Agent 07 — Care Management & Population Health
### HPP AI Agent Suite · status: **Documented** (spec; build follows the Agent 01 pattern)

Identifies care gaps, stratifies risk (HCC/RAF), surfaces SDOH factors, and prepares
outreach and care-plan updates for a care manager. Care-plan writes are gated
(`careplan.update_care_plan`) and require care-manager sign-off; the four-fifths fairness
screen runs on risk-stratification flag/rank output.

**Why it matters.** Population-health and value-based programs depend on closing care gaps
and accurate risk capture; ungoverned risk models raise Section 1557 and CMS risk-
adjustment-integrity concerns, which the fairness screen and grounding controls address.

**Systems (via gateway):** `careplan`, `ehr` (FHIR/HealthLake), `consent`, `kb`.
**Roles:** `CARE_MANAGER`. **Key regs:** HIPAA, CMS risk adjustment integrity, NCQA,
Section 1557, 42 CFR Part 2 (SUD consent).
**Workflow:** identify cohort/gaps → stratify risk → fairness check → draft outreach/plan →
compliance check → **care-manager sign-off gate**.
