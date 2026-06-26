# Agent 08 — Compliance Mapping: Contact Center / Member Services

| Obligation | How this agent satisfies it |
|---|---|
| **Identity before disclosure** | `verify_member` gates all account-specific disclosure; an unverified inquiry returns `VERIFY_IDENTITY` and discloses nothing. |
| **HIPAA Privacy — minimum necessary** | Reads only the member, claim-status, and eligibility data needed; every call is gateway-authorized with a tool-scoped token. |
| **HIPAA Security — audit controls** | Every decision is recorded in the append-only, PHI-masked audit log with lineage and the approving rep. |
| **No autonomous consequential action** | `review_gate` is framework-enforced; `contactcenter.log_interaction` and `create_grievance` are high-risk and require a verified rep approval. The agent cannot submit an appeal (`payer.submit_appeal` not granted). |
| **Section 1557 / language access / health literacy** | Member responses pass a 6th–8th grade plain-language pre-flight; qualified-interpreter language access is a customer configuration. |
| **Grievance & appeals process** | A grievance is intaked and routed for human handling with an acknowledgement timeframe; the outcome is the plan's process, not the agent's. |
| **Grounded member communication** | Grounding fails any response stating a claim status, benefit, amount, or date not present in the retrieved record. |
| **TCPA (outbound)** | Outreach/contact rules remain an operational configuration; this agent handles inbound member-initiated inquiries. |

## Customer responsibilities
CSV for the intended use; IdP mapping of `MEMBER_SERVICES_REP`; live Amazon Connect and payer
status/eligibility connector validation; Guardrail configuration; the grievance/appeals SOP and
language-access program; and prompt/model change control (the registry hash-pins the member
prompts).
