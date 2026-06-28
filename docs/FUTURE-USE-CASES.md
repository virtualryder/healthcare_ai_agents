# Future Use Cases — Extensions on the Same Governed Platform

The eight shipped agents are not the boundary of the suite — they are the proof that a single
governed pattern (deny-by-default MCP gateway, withheld consequential authorities, bound human
gate, hash-chained PHI-masked audit, in-account Bedrock under the AWS BAA, grounding + fairness +
consent) generalizes across healthcare administration. This document sketches **six additional
agents/extensions** that reuse that platform unchanged. Each is a candidate, not a shipped agent;
each keeps its consequential action with a licensed human.

For all six: the AWS building blocks are the same accelerator core — Cognito/IdP for identity,
the MCP authorization gateway for least-privilege tool access, Step Functions (`waitForTaskToken`)
or Fargate for the runtime and human gate, DynamoDB + S3 Object Lock for the append-only WORM
audit, KMS for keys, and Amazon Bedrock + Guardrails (via VPC endpoint, no PHI egress) for
inference. Below, "AWS blocks" highlights anything **additional**.

---

## 1. Pharmacy Prior-Auth / Specialty-Drug Coordination
- **Workflow** — intake a specialty-drug or step-therapy PA request; assemble clinical criteria
  (diagnosis, prior therapies, labs), draft the PA against the plan's formulary/policy, and route
  to the pharmacist or PA nurse. Surfaces step-therapy exceptions and likely missing evidence.
- **Consequential action that stays human** — the **pharmacist / PA nurse submits** the PA, and
  the **coverage determination remains the plan's**; the agent never auto-approves or auto-denies.
- **AWS blocks (additional)** — NCPDP SCRIPT / pharmacy-benefit connector alongside Da Vinci
  CRD/DTR/PAS; formulary knowledge base for grounding.
- **Key regs** — CMS-0057-F (electronic PA), HIPAA, plan/PBM policy, state step-therapy laws.

## 2. Clinical-Trial Matching
- **Workflow** — screen a patient's chart (via FHIR) against trial eligibility criteria, produce a
  ranked, **explained** match list with the criteria met/unmet, and route to the research
  coordinator. Runs a fairness screen on who gets surfaced.
- **Consequential action that stays human** — the **research coordinator / investigator** decides
  eligibility and contacts the patient; the agent only **suggests and explains**, never enrolls.
- **AWS blocks (additional)** — Amazon HealthLake for the normalized FHIR record; a trial-registry
  corpus for grounding; the four-fifths **fairness screen** on the match ranking (as in agents
  05/07).
- **Key regs** — HIPAA, 42 CFR Part 2 (if SUD data), 21st Century Cures, IRB/Common Rule, Section
  1557 (equitable access).

## 3. Provider Credentialing & Enrollment
- **Workflow** — gather and verify provider data (licensure, DEA, board certification, sanctions/
  exclusion lists), assemble the credentialing packet, flag gaps and discrepancies, and route to
  the credentialing committee.
- **Consequential action that stays human** — the **credentialing committee / medical staff
  office** grants or denies privileges and panel enrollment; the agent **verifies and assembles**,
  it never credentials.
- **AWS blocks (additional)** — primary-source-verification connectors (state boards, OIG/SAM
  exclusion lists, CAQH); grounding against the verified sources so no status is asserted untraced.
- **Key regs** — NCQA credentialing standards, CMS enrollment rules, OIG/GSA exclusion screening,
  HIPAA, state licensure law.

## 4. Risk-Adjustment Coding (HCC) Audit
- **Workflow** — review submitted HCC/risk-adjustment codes against the chart for documentation
  support, flag **unsupported or under-documented** diagnoses (both over- and under-coding), and
  route to the coding auditor with the supporting/contradicting chart evidence.
- **Consequential action that stays human** — the **coding auditor / compliance reviewer** decides
  whether to add, delete, or defend a code and whether to amend a submission; the agent **flags
  only** — no resubmission, no deletion.
- **AWS blocks (additional)** — encoder reference (ICD-10/HCC mappings) for grounding; the same
  flags-only gate as Agent 06.
- **Key regs** — False Claims Act / OIG, CMS RADV audit rules, HIPAA, coding-integrity policy.

## 5. SDOH Referral & Closed-Loop
- **Workflow** — identify social-determinant needs (food, housing, transportation) from screening
  data, match to community-based organizations, generate a referral, and **track the loop to
  closure**; escalate stalled referrals to the care team.
- **Consequential action that stays human** — the **care manager / community-health worker**
  authorizes the referral and any benefit action; the agent **drafts and tracks**, it does not
  enroll a member in a benefit or share data without consent.
- **AWS blocks (additional)** — a closed-loop referral connector (e.g., to a community-resource
  network); the **AAL-gated consent ledger** (sensitive needs are 42 CFR Part 2 / minimum-
  necessary sensitive); fairness screen on who is surfaced for outreach.
- **Key regs** — HIPAA minimum-necessary, 42 CFR Part 2, Section 1557, state social-services
  consent rules.

## 6. Quality / HEDIS Abstraction
- **Workflow** — abstract chart evidence for HEDIS / quality measures (e.g., gap closure for
  screenings and chronic-care measures), produce a measure-by-measure evidence summary, and route
  to the quality abstractor for sign-off before a measure is reported.
- **Consequential action that stays human** — the **quality abstractor / clinical reviewer**
  confirms each measure; the agent **abstracts and cites evidence**, it never reports a measure as
  met on its own.
- **AWS blocks (additional)** — HealthLake-normalized FHIR for chart reads; a measure-spec
  knowledge base for grounding so every "met/not-met" is traceable to chart evidence.
- **Key regs** — NCQA HEDIS specifications, CMS Star Ratings rules, HIPAA, Section 1557.

---

## Why they reuse the platform unchanged
Each use case is the **same shape**: read systems of record through governed connectors, reason
with grounded Bedrock inference, draft a work product, and **stop at a named human gate** for the
one consequential action — while the audit, PHI masking, consent, and fairness controls apply
identically. New use cases are new connectors, new prompts (hash-pinned), and a named gate — not a
new security model. See `docs/SUITE-ARCHITECTURE.md` and `docs/DEPLOYMENT-MODELS.md`.
