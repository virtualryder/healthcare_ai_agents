# Agent 04 — Patient Access
### HPP AI Agent Suite · status: **Documented** (spec; build follows the Agent 01 pattern)

Handles scheduling, registration, benefits verification, cost estimates, referral status,
and follow-up communications. Patient cost estimates come from a **deterministic** tool
(`registration.estimate_cost`, Good Faith Estimate basis) — never the LLM — and member-
facing text passes the health-literacy / Section 1557 accessibility pre-flight.

**Why it matters.** Access friction drives leakage and no-shows; eligibility/registration
errors are a top upstream cause of the denials Agent 01 cleans up (e.g. CO-27 coverage,
registration defects). The No Surprises Act requires Good Faith Estimates for self-pay/
uninsured patients.

**Systems (via gateway):** `scheduling`, `registration`, `payer` (270/271 eligibility),
`identity`, `consent`, `kb`. **Roles:** `PATIENT_ACCESS_REP`.
**Key regs:** HIPAA, No Surprises Act, Section 1557 (language access/accessibility).
**Workflow:** verify identity → check eligibility → schedule/register → estimate cost →
compliance check → **human gate on writes** → confirm/follow-up.
