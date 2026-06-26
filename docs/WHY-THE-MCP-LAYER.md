# Why the MCP Authorization Layer — Account-Team Explainer

This is the plain-English account-team explainer for the single most important — and most
under-budgeted — part of the HPP AI Agent Suite: the governed MCP authorization gateway.
Use it to explain to an AWS account team or a customer's buying committee why an agent that
**automates a system of record** needs a governed access layer, and why that layer must be
funded in Phase 1, not deferred.

## The core idea in one paragraph

A chatbot that answers questions is low-stakes. The moment an agent **acts on a system of
record** — an EHR, a clearinghouse, a payer portal, a FHIR API — it is no longer answering
questions; it is *doing things* with real consequences: submitting a claim, assembling a
prior authorization, touching a patient record, moving toward a coverage decision. The
question is no longer "is the answer good?" but "**was this agent allowed to do that, on
whose authority, and can we prove it?**" The MCP authorization layer is the part of the
architecture that answers those three questions. Without it, you have an unaccountable
automation pointed at PHI and money.

## The talk track

> "The model is the easy part. The hard part — and the part that makes this deployable in
> healthcare — is the governed access layer between the agent and your systems of record.
>
> It does three things. First, **deny-by-default authorization**: every action the agent
> takes is checked against the intersection of what the agent is allowed to do and what the
> *human it's acting for* is allowed to do. The agent can never exceed the person. Second,
> a **human gate on high-risk writes**: the agent never submits a claim, files a prior auth,
> or issues a coverage decision on its own — a named human approves, and that approval is
> recorded. In fact, the authority to issue a determination is withheld from every agent by
> policy; an adverse recommendation is forwarded to a medical director, never auto-denied.
> Third, a **tamper-evident audit**: every action, every authorization decision, every
> approval is written to an append-only, PHI-masked, write-once record. When your privacy
> officer, a HITRUST assessor, or CMS asks 'who decided this?', you have the answer.
>
> That's not a feature on top of the agent. That *is* the agent's right to operate in
> healthcare."

## Objection handling

| Objection | Response |
|---|---|
| "Can't the model just be told not to do bad things?" | Instructions aren't a control. A prompt can be injected, a model can drift. The gateway enforces authorization in code, deny-by-default — it doesn't rely on the model behaving. |
| "Our EHR already has roles and permissions." | Good — and the gateway *intersects* with them: the agent gets the lesser of its grant and the user's entitlement, so it can never exceed your existing roles. It adds least-privilege scoping and an agent-specific audit your EHR doesn't produce. |
| "This sounds like it slows everything down." | High-risk writes are gated; everything else flows. The gate is the difference between 'pilot' and 'production' in a regulated setting — and it fails *closed*, so a missed approval never ships an unreviewed action. |
| "Can we add governance later, after the pilot proves value?" | The pilot only proves value if it proves the *governed* pattern. Bolting authorization onto a live agent that already touches PHI means re-architecting under audit pressure. Fund it in Phase 1 and every later agent inherits it. |
| "Isn't Bedrock Guardrails enough?" | Guardrails handle content (PII, denied topics, grounding). They don't decide whether *this user* may take *this action* on *this record*, and they don't produce the approval/authorization audit. Guardrails and the gateway are complementary layers. |
| "Who's accountable if the agent gets it wrong?" | The human who approved, on authority the gateway confirmed they hold — and you can prove it from the audit. The architecture is designed so accountability never falls into a gap. |

## Why fund it in Phase 1

The authorization layer is **horizontal** — it is built once and every one of the eight
agents (and every future agent) runs through it. Funding it in Phase 1 means:

1. **The pilot is production-shaped.** You prove the pattern you'll actually run, not a
   toy you'll have to replace.
2. **Compliance is designed in, not retrofitted.** Minimum-necessary access, human
   decision-making, and an audit trail are the law in healthcare AI — building them first
   is cheaper and defensible.
3. **Every later agent is faster and cheaper.** The expensive, hard part is done; agents 02
   through 08 plug into an existing governed layer.
4. **It's the differentiator.** Anyone can demo an agent. The governed access layer is why
   this one is allowed to touch a claim, a chart, or a coverage decision.
