# HPP AI Agent Suite — Statement of Work Template (POC / Pilot)

> A fill-in-the-blank SOW shell for a POC or Pilot engagement. Bracketed `[…]` fields are
> completed per engagement. This template is not legal advice; the SI's contracts team
> finalizes terms. It assumes the offering definitions in `POC-OFFERING.md` /
> `PILOT-OFFERING.md` and the maturity honesty stated throughout this repo.

---

## 1. Parties and term

- **Provider (SI):** [SI legal name]
- **Customer:** [Customer legal name] ("Customer")
- **Effective date:** [date]   **Term:** [4–6 weeks POC | 8–12 weeks Pilot]
- **Engagement type:** [POC | Pilot]   **Lead agent:** [Agent 01 Revenue-Cycle & Denial | other]

## 2. Background and objective

Customer engages SI to [demonstrate / pilot] the [agent] from the HPP AI Agent Suite — a
governed AI-agent accelerator built on AWS. Objective: [e.g., reduce denial rework cost and
recover previously-abandoned denials behind a framework-enforced human gate, with measured
KPIs]. The agent assists, drafts, assembles, flags, and recommends; a licensed or credentialed
Customer employee makes every consequential decision.

## 3. Scope

**In scope:**
- One agent: [agent], configured to Customer's [denial/payer mix | PA workflow | UM criteria].
- Mode: [POC: `EXTRACT_MODE=demo` / `CONNECTOR_MODE=fixture` on synthetic/de-identified data |
  Pilot: in Customer's AWS account, `LLM_PROVIDER=bedrock`, [fixture→live] connectors].
- Governed platform controls: MCP authorization gateway (deny-by-default + least-privilege
  intersection), framework-enforced human-approval gate, short-lived tool-scoped tokens, PHI
  masker (HIPAA Safe Harbor), PHI-masked append-only audit (DynamoDB + S3 Object Lock WORM).
- Deliverables per Section 4.

**Out of scope (unless added by change order):**
- Customer computer-system validation (CSV/CSA); HITRUST certification; penetration test.
- Live-connector validation beyond [named systems]; additional agents or business units.
- Any contractual guarantee of clinical, coverage, or financial outcomes.
- For POC: any PHI processing or production data.

## 4. Deliverables

| # | Deliverable | Acceptance basis |
|---|---|---|
| 1 | Configured running agent ([demo | in-account deployable]) | Demonstration on Customer data shape |
| 2 | Governed-control walkthrough (gateway, HITL, PHI mask, audit) | Review sign-off |
| 3 | Populated ROI value model | Inputs confirmed by Customer sponsor |
| 4 | Target-state AWS architecture | Architecture review sign-off |
| 5 | [Pilot] Measured KPI readout vs. baseline | KPIs per Section 7 |
| 6 | Pilot / production proposal + next-phase SOW outline | Delivered |

## 5. Assumptions

- [POC: synthetic or de-identified data only.] [Pilot: AWS BAA in place; Bedrock enabled in
  Region [x]; IdP federation path identified; data-governance sign-off obtained.]
- Customer provides timely access to SMEs, sample data, and policy/criteria references.
- A named reviewer pool exercises the human gate [Pilot].
- Consequential authorities (claim submission, UM determination, note signature) remain with
  Customer roles ([`BILLER`], [`UM_MEDICAL_DIRECTOR`], signing clinician) and are withheld from the agent.

## 6. Responsibilities matrix (RACI)

| Activity | SI | Customer |
|---|---|---|
| Agent configuration & deployment | R/A | C/I |
| AWS account, BAA, Bedrock enablement | C | R/A |
| IdP / role-entitlement provisioning | C | R/A |
| Sample / de-identified data provision | C | R/A |
| SME review & HITL reviewer staffing | C/I | R/A |
| Governance control validation | R/A | C |
| KPI baseline & measurement [Pilot] | R | A |
| Security / privacy review | C | R/A |

## 7. Acceptance criteria

- **POC:** (a) agent produces grounded, policy-cited drafts judged usable by Customer SME on
  Customer's samples; (b) controls pass first-pass security/privacy review; (c) ROI model
  populated and reviewed. Acceptance is by demonstration and readout.
- **Pilot:** KPIs measured against baseline over the term: [draft acceptance rate], [analyst
  minutes saved per transaction], [throughput on previously-abandoned work], [recovery/overturn
  lift], [100% gate integrity], [audit completeness]. Targets: [PLACEHOLDER per KPI].

## 8. Change control

Any change to scope, deliverables, timeline, connectors, or fees is documented in a written
change order signed by both parties before work proceeds. Connector additions beyond [named
systems] and additional agents/business units are changes.

## 9. Fees and payment

- **Engagement fee:** [PLACEHOLDER — fixed-fee | T&M].
- **AWS run cost [Pilot]:** [pass-through per `TCO-MODEL.md` | Customer-borne in Customer account].
- **Payment schedule:** [milestone | monthly].   **Expenses:** [policy].

## 10. Standard terms (reference)

Confidentiality, data handling under the BAA, IP ownership of SI accelerator vs. Customer
configurations, limitation of liability, and termination per the parties' master agreement
[MSA reference]. The agent does not auto-submit claims/appeals, does not make coverage or
payment determinations, and does not replace Customer staff; SI makes no outcome guarantee.

---

**Signatures:** SI [name/title/date] · Customer [name/title/date]
