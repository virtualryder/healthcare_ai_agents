# HPP AI Agent Suite — Objection Handling

> The objections a healthcare buyer raises, with crisp responses grounded in the platform's
> actual, code-enforced controls — not aspiration. Statistics are source-class tagged and
> traced to `../gtm/HPP-DECK-SOURCES.md`. The governing posture under every answer: AI
> assists, drafts, assembles, flags, and recommends; a licensed or credentialed human decides
> every consequential action, and that boundary is enforced in code, not policy prose.

## 1. "AI can't be allowed to deny care."

Correct — and in this suite it cannot. `payer.issue_determination` is withheld from **every**
agent and is held only by a `UM_MEDICAL_DIRECTOR` role. The UM and prior-auth agents prepare a
criteria-grounded recommendation (MEETS / DOES_NOT_MEET / NEEDS_INFO); an adverse
recommendation is **forwarded** to the medical director, never auto-denied. This is the
technical expression of what CMS expects for AI in coverage decisions.

## 2. "LLMs hallucinate — that's a non-starter in healthcare."

Outputs are grounded against source records and run through grounding verification; prompts
are hash-pinned in a versioned registry so behavior cannot silently drift; Amazon Bedrock
Guardrails filter inputs and outputs; and an eval harness plus a red-team suite gate every
change. Above all, a human reviews every consequential output before it acts — a drafted
appeal, note, or recommendation is never the final word.

## 3. "PHI cannot leave our walls / can't go to an external AI."

With `LLM_PROVIDER=bedrock`, inference runs on HIPAA-eligible Amazon Bedrock — reached
privately over AWS PrivateLink — under your AWS BAA; no PHI egress to an external AI API. The PHI masker (HIPAA Safe Harbor
identifiers) runs at every audit and trace boundary, so PHI does not leak into logs either.
The provider-abstracted LLM factory makes Bedrock a configuration switch, not a re-architecture.

## 4. "How do we know an agent won't access more than it should?"

The MCP authorization gateway is deny-by-default with a least-privilege intersection:
`permitted(tool) ⇔ tool ∈ AGENT_TOOL_GRANTS[agent] ∩ ROLE_ENTITLEMENTS[user_roles]`. An agent
can never exceed the human on whose behalf it acts, and tokens are short-lived and tool-scoped
— there are no standing service accounts. This is enforced in the gateway, outside the model;
a prompt cannot widen it.

## 5. "Who is accountable when something goes wrong?"

A licensed or credentialed human makes every consequential decision, and the withheld tools
enforce it: a revenue-cycle agent cannot submit a claim (a `BILLER` does); a UM agent cannot
issue a determination; a clinical note is a draft a clinician signs; the payment-integrity
agent flags only — no recoupment or submission. The PHI-masked append-only audit trail binds
the reviewer's verified identity into the record for every gated action.

## 6. "Payer algorithmic-UM is under regulatory scrutiny — won't this make it worse?"

It is designed to make an AI-in-UM deployment defensible. The determination authority stays
with your medical director; the agent only assembles criteria and grounds a recommendation. A
four-fifths fairness screen runs on UM and risk-stratification outputs, every step is captured
in the immutable audit trail, and the recommendation is transparent and source-cited. That is
a stronger posture than an opaque rules engine, not a weaker one.

## 7. "Integration with our EHR/clearinghouse will cost a fortune."

We size connector effort in the Assessment up front. The 14-system connector framework runs
fixture-then-live with **identical method signatures**, so the path from demo to live is
configuration (`CONNECTOR_MODE`, `EXTRACT_MODE`), not a rewrite. The gateway never knows which
backend is live, which keeps integration scoped and testable rather than open-ended.

## 8. "We're locked into our EHR vendor — why not just use their AI add-on?"

EHR-native add-ons lock you to one vendor's surface, rarely span payer-side UM/claims, and
don't give you a portable, inspectable authorization gateway under your own BAA. This suite's
gateway semantics are replicated in `platform_core/` — readable and testable without an AWS
account — and run across your systems, not just one EHR. You keep the control plane.

## 9. "The validation burden for AI in a clinical environment is huge."

Agreed — which is why we are explicit that production-readiness (customer computer-system
validation CSV/CSA, live-connector validation, penetration test, HITRUST) is the **engagement**,
not a day-one claim. The accelerator gives validation a head start: governance is built and
tested (185 automated tests as of 2026-07-07, no API key), controls are mapped regime→control→AWS service, and
the human gate and audit trail are the evidence surfaces a validation effort needs.

## 10. "Couldn't we just build this ourselves?"

You could wire an LLM call. The expensive, slow part is the governance scaffolding —
deny-by-default authorization, the framework-enforced human gate, PHI masking, the append-only
audit, grounding, prompt pinning, fairness, accessibility, and the regime→control→AWS mappings
— built once and reused across eight agents. Building that to a defensible standard, then
re-deriving it per workflow, is where in-house efforts stall.

## 11. "Show me it actually enforces the human gate — not just documents it."

The gate is framework-enforced: high-risk write tools block until a verified reviewer identity
is bound into the record — `interrupt_before=["human_review_gate"]` in LangGraph, a Step
Functions `waitForTaskToken` task in the AWS-native build. Application code cannot bypass it.
We demonstrate it live in the POC/pilot.

## 12. "What about audit and tamper-evidence for the HIPAA Security Rule?"

The audit trail is append-only by construction: DynamoDB denies Update and Delete, and S3
Object Lock provides WORM immutability for the retained record. The PHI masker ensures no Safe
Harbor identifier lands in the trail. This supports the HIPAA Security Rule's audit-control and
integrity requirements with a tamper-evident record.

## 13. "Patients have a right to non-discrimination — how do you address Section 1557?"

Risk-stratification and UM outputs run through a four-fifths fairness screen, and member/patient
communications run through accessibility and health-literacy checks. These align with the HHS
Section 1557 nondiscrimination rule `[gov]`, and the results are reported in governance reviews.

## 14. "We're a payer staring at CMS-0057-F — does this help or distract?"

It helps. The rule requires four FHIR APIs (Patient Access, Provider Access, Payer-to-Payer,
Prior Authorization) by Jan 1, 2027, with operational, PA denial-reason/turnaround, and metrics
provisions due Jan 1, 2026 `[gov]`. Agents 02 and 05 are built around the prior-auth and UM
workflows the rule reshapes, on FHIR-native AWS services (HealthLake), with the determination
control that keeps the deployment defensible. 93% of plan execs expect AI to ease prior auth
`[industry-research]` — this is how to do it under governance.

## 15. "What if the model gives a bad recommendation and a clinician trusts it?"

The output is decision-support, presented as a grounded, source-cited draft or recommendation
for a credentialed human to evaluate — never an executed action. The withheld authorities,
the human gate, grounding verification, and the audit trail together ensure the human remains
the decision-maker. We measure draft acceptance and edits in the pilot rather than assuming the
model is right.
