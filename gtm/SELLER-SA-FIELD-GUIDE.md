# Seller & Solutions-Architect Field Guide — HPP AI Agent Suite

A phase-by-phase playbook for the seller and the partner/AWS Solutions Architect taking the
**HPP AI Agent Suite ("HCOS")** from a first conversation to a production agent. The suite is
honest about its maturity: it is **Demonstrated and Deployable-by-design** today (258 tests as of
2026-07-10, no API key — 8 agents + governance + platform_core security + care_platform + golden path), and
production-readiness (CSV/CSA validation, IdP federation, live connectors, penetration test,
HITRUST/SOC 2) is the **engagement**. An executed **AWS BAA** precedes any PHI. Cite all external
numbers from `gtm/HPP-DECK-SOURCES.md` / `SOURCES.md`; never invent competing figures.

## The one-sentence pitch
> A governed accelerator for healthcare AI agents on AWS that automates the administrative work
> around claims, prior auth, and care — while a deny-by-default authorization gateway and a named
> human gate keep every consequential decision with a licensed person and every action on a
> tamper-evident, PHI-masked audit trail.

---

## Phase 0 — Qualify

Confirm there is a real, expensive, repeatable administrative workflow and an owner who can fund
a POC. The flagship wedge is **Agent 01 (Revenue-Cycle & Denial)** for providers and **Agent 05
(Utilization Management)** / **Agent 02 (Prior Authorization)** for plans.

### Opening lines by buyer

| Buyer | Opening line |
|---|---|
| **CFO / VP Revenue Cycle** (provider) | "Initial denials are running ~11.8% and climbing, and a third to over half of denied claims are never reworked. We can stand up an agent that drafts the appeal packet and root-causes the denial code — but it never submits a claim; your denials specialist still owns that. Want to see the human gate hold?" |
| **CMIO / VP Clinical Ops** (provider) | "Your clinicians are doing documentation and prior-auth chase work that burns them out. We draft the note and the PA packet inside your governance; the clinician signs off, and the agent has no order-entry authority. Ambient-AI pilots have moved burnout from ~52% to ~39% — but only when the clinician stays in control." |
| **Health-plan VP, UM / Claims** | "CMS now expects you to be careful about AI in utilization management, and CMS-0057-F puts FHIR PA APIs on the clock for Jan 1 2027. Our UM agent can summarize against MCG/InterQual and run a four-fifths fairness screen — but issuing the determination is withheld from every agent; an adverse recommendation is forwarded to your medical director, never auto-denied." |
| **CISO / Privacy Officer** | "Before we talk use cases: authorization here is structural, not prompt-based. Deny-by-default gateway, consequential tools withheld from every agent, bound single-use approvals, a hash-chained WORM audit, PHI masking, and in-account Bedrock under your AWS BAA. I can walk your team through the threat model and the NIST control matrix line by line." |

### Qualifying questions
- **Economics** — "What's your initial denial rate, and your cost to rework a denied claim?"
  (Anchor: rework $25–$181 by complexity; ~$18B/yr spent overturning denials industry-wide.)
- **Denial mix** — "Which denial codes dominate — **CO-197** (no/invalid prior auth), **CO-50**
  (not medically necessary), **CO-16** (missing/incorrect info)?" The mix tells you whether the
  wedge is Agent 01, Agent 02, or upstream patient access (Agent 04).
- **Systems of record** — "Which EHR — **Epic**, **Oracle Health**, **MEDITECH**? Which
  clearinghouse — **Change Healthcare**, **Availity**, **Waystar**?" (Drives connector scope and
  X12 837/835/277 work.)
- **Regulatory clock** — "Where are you on **CMS-0057-F** FHIR PA-API readiness for Jan 1 2027?"
- **Consequential authority** — "Today, who holds the authority to submit the claim / issue the
  determination / sign the note — and could you point an auditor to where that decision is
  recorded?" (This is the question that sells the human gate.)
- **AWS posture** — "Is your **AWS BAA** executed, and is **Amazon Bedrock model access enabled
  in your Region**?" No BAA, no PHI — fixture mode only until it is in place.

**Qualified when:** a named workflow + a funding owner + a security stakeholder who will review,
and AWS BAA either in place or in motion.

---

## Phase 1 — Discover

Map the workflow and the authority boundary. Produce: the target agent(s), the named human gate,
the systems to connect, the IdP roles to map, and the one withheld authority you will demo. Pull
the per-agent detail from `deliverables/agent-handbooks/<agent>-HANDBOOK.md`. Confirm whether the
opportunity is single-agent (standalone stack) or a journey that spans agents (platform — see
`gtm/HPP-PLATFORM-GTM-STORY.md`).

---

## Phase 2 — Workshop (half-day, technical + compliance)

Run two tracks in parallel:
- **Architecture** — walk `docs/SUITE-ARCHITECTURE.md`, `docs/DEPLOYMENT-MODELS.md`, and the
  per-agent VPC isolation (CIDRs 10.30–10.37). Decide gateway mode (`portable` vs `agentcore`)
  and deploy mode (`native` Step Functions vs `container` Fargate).
- **Security** — run the CISO checklist below against the evidence. End the workshop with the
  no-API-key demo so the room watches the gate suspend and the deny-by-default policy fire.

---

## Phase 3 — POC (2–4 weeks, fixture mode, no PHI)

Deploy one agent's isolated stack via `scripts/deploy.sh` (see the handbook), seed Cognito roles,
and run the human-gate smoke test end to end: gated write → **suspends** at the named gate → HITL
item appears → approve → action proceeds and is written to the append-only audit → reject →
action does not proceed → out-of-scope tool call → **denied by default**. Success criteria are
the controls holding, not model cleverness. No PHI in fixture mode.

---

## Phase 4 — Pilot (engagement, limited PHI under BAA)

Now the production work begins: AWS BAA + SI BAA executed; enterprise **IdP federated** to
Cognito with `custom:hpp_role` mapped to real roles; **live connectors** validated against the
real EHR / clearinghouse / payer / FHIR APIs; **Guardrail** thresholds tuned; **CSV/CSA**
validation signed off by the healthcare org; HITL queue SLAs ratified. Measure against the
customer's own baseline (denial overturn rate, time-to-appeal, PA turnaround).

---

## Phase 5 — Production

Penetration test and red-team complete; **HITRUST/SOC 2** evidence package assembled from the
control mappings; observability wired to the customer's monitoring; runbooks adopted (incident
response, DR with ratified RPO/RTO, model-degradation change control). Then expand.

---

## Land and expand

1. **Land** with **Agent 01 (denials)** for providers — the clearest dollar ROI and the easiest
   human gate to demonstrate (it cannot submit a claim).
2. **Expand provider-side** to **Agent 02 (prior authorization)** and **Agent 04 (patient
   access / Good Faith Estimate)** — same governed stack, adjacent workflows, shared connectors.
3. **Cross to the plan** with **Agent 05 (utilization management)** and **Agent 08 (contact
   center / member services on Amazon Connect)** — the payer-side wedge, anchored on CMS AI-in-UM
   guidance and CMS-0057-F.
4. **Orchestrate** only when several agents are live: adopt the Care & Claims Orchestration
   Platform agent-by-agent so a denial becomes an appeal becomes a member notification — without
   widening any agent's authority (`ENTERPRISE-PLATFORM.md`).

---

## § CISO security-review checklist

A numbered checklist a CISO or AppSec reviewer runs against the accelerator. Each line names
where it is evidenced. (Maturity caveat: the Python control plane is a **reference model** of the
production AgentCore Gateway / API Gateway + Cedar authorizer; the production authorizer must be
tested, not just this analog.)

1. **Cryptographic identity / JWT verification** — RS256/JWKS with an algorithm allow-list and an
   alg-confusion guard; client-supplied roles never trusted.
   *Evidence:* `SECURITY.md` §1; `docs/THREAT-MODEL.md` T1; `docs/NIST-800-53-CONTROL-MATRIX.md`
   IA-2/IA-5; `platform_core/.../jwt_verify.py`; control-plane `test_security_controls`.
2. **Deny-by-default authorization + withheld authorities** — permitted ⇔ agent grant ∩ user
   entitlement; consequential tools (submit a claim, issue a UM determination) withheld from
   every agent and proven by tests.
   *Evidence:* `SECURITY.md` §2; `THREAT-MODEL.md` T2–T4; `NIST...` AC-3/AC-6;
   `OWASP-LLM-ATLAS-MAPPING.md` LLM06; `mcp_gateway/policy.py`; gateway tests.
3. **Bound, single-use separation-of-duties approvals** — approval token cryptographically bound
   to the exact tool + arguments; jti replay guard; expiry; reviewer ≠ requester.
   *Evidence:* `SECURITY.md` §3; `THREAT-MODEL.md` T5–T6; `NIST...` AC-5; `approvals.py`;
   `test_security_controls`.
4. **Hash-chained append-only audit + WORM** — chained records (`verify_chain`); prod conditional
   writes + IAM Update/Delete deny + S3 Object Lock COMPLIANCE.
   *Evidence:* `SECURITY.md` §5; `THREAT-MODEL.md` T7; `NIST...` AU-9/AU-10; `mcp_gateway/audit.py`,
   `audit_sinks.py`, `infra/cloudformation/data.yaml`.
5. **PHI masking + Bedrock via PrivateLink under BAA** — fail-closed Safe-Harbor masking at every
   audit/trace boundary; Bedrock via VPC endpoint, no PHI egress to external AI APIs.
   *Evidence:* `SECURITY.md` §6–7; `THREAT-MODEL.md` T8; `OWASP...` LLM02; `phi.py`,
   `llm_factory.py`, `tracing.py`.
6. **Bedrock Guardrails** — PHI filters + unauthorized-determination denied topic on input and
   output. *Evidence:* `docs/DEPLOY-QUICKSTART.md` §2; `NIST...` SI-10; `OWASP...` LLM01/LLM05;
   security stack.
7. **Grounding verification** — any code/amount/policy not traceable to a governed source fails.
   *Evidence:* `THREAT-MODEL.md` T10; `OWASP...` LLM09; `governance/grounding.py`.
8. **Fairness screen** — four-fifths screen on flag/rank in UM and risk-strat; adverse action
   never automated. *Evidence:* `THREAT-MODEL.md` T12; agents 05/07; `governance/fairness`.
9. **42 CFR Part 2 consent** — consent checked before sensitive (SUD / behavioral-health)
   disclosure; escalate without consent. *Evidence:* `THREAT-MODEL.md` T15; agents 03/07
   `check_consent`; `care_platform/.../consent.py` (AAL2-gated).
10. **IdP integration** — Cognito user pool with `custom:hpp_role`, federated to the enterprise
    IdP; entitlement source of truth is customer-owned. *Evidence:* `NIST...` AC-2;
    `SECURITY.md` out-of-scope; `DEPLOY-QUICKSTART.md` §5.
11. **Penetration test / red-team** — customer-engagement scope; structural-injection red-team
    scenarios ship. *Evidence:* `THREAT-MODEL.md` residual risk; `governance/redteam/`;
    `NIST...` RA-5.
12. **HITRUST / SOC 2** — evidence package assembled from the control mappings; authorization is
    customer-engagement work. *Evidence:* `NIST-800-53-CONTROL-MATRIX.md`;
    `governance/controls/control_mappings.py`; `docs/COMPLIANCE-CONTROL-MAPPINGS.md`.
