# Care & Claims Orchestration Platform — GTM Story

The pitch for the **platform** layer, for the moment a buyer realizes that a single agent solves a
single step but their actual problem is a **journey** that crosses several. References:
`ENTERPRISE-PLATFORM.md` and `care_platform/hpp_care_platform/`.

## The fragmentation problem
A patient or member event almost never lives inside one workflow. A **denial** becomes an
**appeal**, then a **member notification**. An **admission** becomes a **discharge note draft**,
a **care-plan update**, and a **follow-up visit**. A **new member** moves from **eligibility** to
**registration** to **care-gap outreach**. Each of those steps belongs to a different agent, a
different system of record, and often a different team. When the steps are stitched together by
people copying data between portals, the journey is slow, the audit trail is fragmented across
systems, and consent and authority boundaries blur at exactly the hand-offs where they matter
most.

Standalone agents fix the steps. They do not, on their own, fix the **seams**.

## The narrative
> You already trust each agent inside its own governed stack — it does its job and stops at a
> named human gate. The platform is the thin, governed layer that **sequences** those agents
> across a journey and **cleans up** when a downstream system fails — without ever giving an
> agent a tool it doesn't already hold. Orchestration here is about ordering governed actions and
> compensating cleanly, not about new power.

The platform adds exactly five capabilities and, deliberately, **nothing that widens authority**:
1. **Govern (ADR-001)** — every platform step runs through the **same MCP authorization gateway**
   with the **same acting-user claims** as standalone agents. A passing test asserts a journey
   step calling a withheld tool (`payer.issue_determination`) is **denied**.
2. **Canonical record + adapters** — one normalized view of subject / plan / claim / encounter
   across EHR, clearinghouse, payer, and contact center (`canonical.py`).
3. **Consent ledger** — AAL-gated, 42 CFR Part 2 aware; a sensitive scope requires **AAL2** and
   an explicit grant or the journey **escalates** rather than proceeding (`consent.py`).
4. **Durable saga with compensation** — a journey is a saga; on failure the completed steps'
   compensating actions run **in reverse**; a high-risk write **suspends** at the human gate
   (`saga.py`; AWS-native = Step Functions, `Catch`→compensate, `waitForTaskToken` gate).
5. **Compliance event bus** — every forward and compensating step emits a **PHI-masked,
   hash-chained** evidence event reusing the gateway's tamper-evident chain (`events.py`).

### Journeys shipped (run with no API key)
| Journey | Agents spanned | Demonstrates |
|---|---|---|
| `denial_to_resolution` | 01 → 06 → 01 → 08 | gateway authority preserved; suspends at the denials-specialist + member-services gates |
| `admission_to_followup` | 05 → 03 → 07 → 04 | clinician sign-off, care-manager sign-off, access-rep approval in sequence |
| `new_member_onboarding` | 04 → 04 → 07 | eligibility → gated registration → care-gap identification |

## Buyer personas
- **VP / SVP, Revenue Cycle (provider)** — owns denial→appeal→notification end to end; feels the
  hand-off cost. Platform value: one auditable thread from denial to member letter.
- **Chief Medical / Care-Operations Officer (provider)** — owns admission→discharge→care-plan→
  follow-up; wants the clinical sign-offs sequenced, not bypassed.
- **Chief Digital / Transformation Officer (plan or system)** — owns the cross-functional journey
  and the CMS-0057-F / interoperability roadmap; buys the orchestration narrative.
- **CISO / Chief Compliance Officer** — must be convinced orchestration is not a back door; the
  ADR-001 "same gateway, same claims" property is written for them.

## Objection-handling Q&A
- **"Does orchestration widen an agent's authority?"** No. Every platform step authorizes through
  the **same gateway** with the **same acting-user claims**; the deny-by-default intersection,
  withheld tools, and bound human gate apply identically. The proof is a test: a journey step that
  calls `payer.issue_determination` is denied. An A2A hop is a convenience, never a back door.
- **"What if a step in the middle of a journey fails?"** The saga **compensates** — completed
  steps' compensating actions run in reverse, so there are no half-finished journeys. The
  AWS-native form is a Step Functions `Catch`→compensate path.
- **"How do you handle sensitive data crossing teams or agencies?"** The **AAL-gated consent
  ledger** records and checks consent before any disclosure; a 42 CFR Part 2 / SUD /
  behavioral-health scope requires **AAL2** plus an explicit grant, and absent that the journey
  **escalates** instead of proceeding.
- **"Is the human still in the loop across a multi-step journey?"** Yes — a high-risk write
  **suspends** the journey at the human gate exactly as the agent-level gate does
  (`waitForTaskToken`); the journey resumes only after the named reviewer approves.
- **"Can we adopt this without re-platforming?"** Yes — **standalone first, platform when ready**.
  Adopt agent by agent; the same agents become saga steps unchanged. See `docs/DEPLOYMENT-MODELS.md`.

## Stance
Lead with standalone agents and dollar ROI. Introduce the platform once two or more agents are
live and the customer feels the seams. The platform is the expansion motion, not the entry point.
