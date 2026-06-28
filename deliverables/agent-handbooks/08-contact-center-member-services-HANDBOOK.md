# Agent Handbook — 08 Contact Center / Member Services

Assists member-services reps on Amazon Connect — with an identity gate before any disclosure — and
**cannot submit an appeal**. Maturity: Demonstrated + Deployable-by-design; production-readiness
(CSV/CSA, IdP, live connectors, pen test, HITRUST) is the engagement; AWS BAA precedes any PHI.

## Workflow + human gate
Take a member contact on **Amazon Connect** → **verify member identity before any disclosure** →
retrieve account/claim/benefit context through governed connectors → draft a response or next-step
summary → **suspend at the Member-Services-Rep gate** for any consequential action. **Named human
gate:** Member-Services Rep. A live agent call costs ~$25–$35 — the value is faster, accurate,
governed assistance, not autonomous action.

## Systems / connectors (with standards)
- **Contact center** — **Amazon Connect** (voice/chat) as the channel.
- **EHR / FHIR + Payer** — member, coverage, claim status via FHIR (Amazon HealthLake) and **X12
  276/277** (claim status), **270/271** (eligibility).
- **Identity** — member identity verification before disclosure.

## Workforce roles to map in the IdP
`MEMBER_SERVICES_REP` (the gate). Map to `custom:hpp_role`.

## Withheld authority (what it never does)
**Cannot submit an appeal** and **never discloses member data without passing the identity gate.**
The agent assists and drafts; the Member-Services Rep owns any consequential action (including
appeal submission, which is withheld from the agent).

## Deploy (fixture mode, no PHI)
```
scripts/build_lambdas.sh
scripts/deploy.sh 08-contact-center-member-services dev portable native s3://my-cfn-staging/hpp 10.37.0.0/16
```
- Params: `infra/cloudformation/params/08-contact-center-member-services.json` · Terraform:
  `terraform apply -var-file=envs/08-contact-center-member-services.tfvars`
- VPC CIDR `10.37.0.0/16`.

## Human-gate smoke test
1. Attempt a disclosure **before** identity verification → confirm the **identity gate** blocks it.
2. Sign in as a seeded `MEMBER_SERVICES_REP`; verify identity; retrieve context.
3. Drive a consequential action → run **suspends** at the Member-Services-Rep gate; approve →
   proceeds and is written to the **append-only PHI-masked audit**; reject → no action.
4. Attempt an appeal-submission tool → **denied by default** (withheld).

## Key regs
HIPAA Privacy/Security, HITECH; **Section 1557** (language access / nondiscrimination); CMS
member-communication rules; identity-proofing best practice.

## Go-live checklist
- [ ] AWS BAA + SI BAA executed; no PHI before both.
- [ ] IdP federated; `MEMBER_SERVICES_REP` mapped to `custom:hpp_role`.
- [ ] **Amazon Connect** integrated; FHIR + X12 276/277/270/271 connectors validated.
- [ ] Identity-proofing flow validated; Section 1557 language access reviewed.
- [ ] CSV/CSA signed off; HITL SLA ratified; Guardrail tuned.
- [ ] Pen test + HITRUST/SOC 2 evidence assembled; observability + runbooks adopted.
