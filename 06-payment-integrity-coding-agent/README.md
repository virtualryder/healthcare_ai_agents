# Agent 06 — Payment Integrity & Coding
### HPP AI Agent Suite · status: **Documented** (spec; build follows the Agent 01 pattern)

Suggests and validates codes (ICD-10, CPT/HCPCS), runs NCCI/MUE edits and DRG checks,
and flags overpayments / duplicates for human payment-integrity review. The agent
**flags**; it never recoups, adjusts payment, or submits — those remain human decisions
(`pas.update_case` is the only gated write, for adding a review note).

**Why it matters.** Coding defects are a leading denial root cause (feeding Agent 01) and
a False Claims Act exposure surface; payment-integrity recoveries are a measurable payer
outcome. Grounding ensures a suggested code is traceable to documentation, not invented.

**Systems (via gateway):** `coding` (encoder, NCCI/MUE, LCD/NCD), `pas`, `clearinghouse`,
`ehr`, `kb`. **Roles:** `CODING_SPECIALIST`. **Key regs:** HIPAA, CMS NCCI, False Claims
Act, OIG guidance.
**Workflow:** load claim/encounter → suggest/validate codes → necessity check →
flag overpayment/duplicate → compliance check → **human review gate**.
