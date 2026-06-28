# HPP Enterprise Platform — the Care & Claims Orchestration layer

The eight agents each run standalone, with their own governed stack. The **Care & Claims
Orchestration Platform** (`care_platform/hpp_care_platform/`) is the optional layer that
coordinates them across a patient/member journey that spans the health system or plan — a
**denial that becomes an appeal and a member notification**, an **admission that becomes a
discharge draft, a care-plan update, and a follow-up visit**, a **new member onboarded** from
eligibility through care-gap outreach.

It adds five capabilities — and, deliberately, **nothing that widens authority**.

## 1. Govern — the platform never bypasses the gateway (ADR-001)
Every platform action runs through the **same MCP authorization gateway** with the **same
acting-user claims** as the standalone agents (`care_platform/.../govern.py`). So the
deny-by-default intersection, the bound human-approval gate, scoped tokens, and the PHI-masked
audit apply identically to platform-initiated actions. A passing test asserts a journey step
calling a withheld tool (`payer.issue_determination`) is denied — orchestration cannot escalate
privilege. This is the single most important property: an A2A hop is a convenience, never a
back door.

## 2. Canonical record + adapters
One normalized view (`canonical.py`) of subject / plan / claim / encounter across the EHR,
clearinghouse, payer, and contact center, so steps reason over consistent fields instead of
re-deriving them from each connector's shape.

## 3. Consent ledger — AAL-gated, 42 CFR Part 2 aware
Before a journey discloses or acts on sensitive data it records and checks consent
(`consent.py`): a sensitive scope (SUD / behavioral-health / 42 CFR Part 2) requires **AAL2**
assurance and an explicit grant, else the journey **escalates** rather than proceeding.

## 4. Durable saga with compensation
A journey is a saga (`saga.py`): steps run in order; if a step fails, the completed steps'
**compensating actions run in reverse** — no half-finished journeys. A high-risk write
**suspends** the journey at the human gate (just like the agent-level gate) rather than
proceeding. The AWS-native form is a **Step Functions** state machine: compensation is a
`Catch` → compensate path, the human gate is `waitForTaskToken`
(`aws-native-reference/care-platform/`).

## 5. Compliance event bus
Every forward and compensating step emits a **PHI-masked, hash-chained** evidence event
(`events.py`, reusing the gateway's tamper-evident audit chain) — the auditable record a
reviewer or regulator reads to reconstruct exactly what happened, step by step.

## Journeys shipped
| Journey | Agents spanned | Demonstrates |
|---|---|---|
| `denial_to_resolution` | 01 → 06 → 01 → 08 | gateway authority preserved; suspends at the denials-specialist + member-services gates |
| `admission_to_followup` | 05 → 03 → 07 → 04 | clinician sign-off, care-manager sign-off, access-rep approval in sequence |
| `new_member_onboarding` | 04 → 04 → 07 | eligibility → gated registration → care-gap identification |

Run them (no API key):
```bash
PYTHONPATH=platform_core:care_platform python aws-native-reference/care-platform/local_runner.py
```

## Stance — standalone first, platform when ready
Adopt the platform **agent by agent**; the same agents become saga steps unchanged. Nothing in
the platform requires giving an agent a tool it doesn't already hold — the orchestration is
purely about sequencing governed actions and compensating cleanly when a downstream system
fails. See `docs/DEPLOYMENT-MODELS.md`.
