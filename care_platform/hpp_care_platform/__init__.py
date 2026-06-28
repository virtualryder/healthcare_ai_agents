"""
hpp_care_platform — the Care & Claims Orchestration Platform.

The eight agents each run standalone. This optional layer coordinates them across a
patient/member journey that spans agencies of the health system or plan — a denial
that becomes an appeal, an admission that becomes a discharge plan and follow-up, a
new member who needs eligibility, registration, and care-gap outreach. It adds five
things on top of the agents, and NOTHING that widens authority:

  * govern   — every platform action runs through the SAME MCP gateway with the SAME
               acting-user claims, so deny-by-default + the human gate still apply.
  * canonical — one normalized patient/member/claim record across systems of record.
  * consent  — an AAL-gated consent ledger (incl. 42 CFR Part 2) checked before any
               sensitive disclosure.
  * saga     — a durable, compensating workflow: if a step fails, completed steps are
               compensated in reverse (no half-finished journeys).
  * events   — a compliance event bus: every step emits a PHI-masked, hash-chained
               evidence event.

The platform is additive — adopt it agent by agent; the same agents become saga steps
unchanged.
"""
__version__ = "0.1.0"
