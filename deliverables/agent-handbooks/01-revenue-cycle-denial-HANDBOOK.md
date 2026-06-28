# Agent Handbook — 01 Revenue-Cycle & Denial

The flagship land agent. Drafts denial work product and root-causes denial codes for a provider's
revenue-cycle team — and **cannot submit a claim**. Maturity: Demonstrated + Deployable-by-design;
production-readiness (CSV/CSA, IdP, live connectors, pen test, HITRUST) is the engagement; AWS BAA
precedes any PHI.

## Workflow + human gate
Ingest a denied/remittance record → classify the denial (e.g. CO-197 no/invalid prior auth, CO-50
not medically necessary, CO-16 missing/incorrect info) → pull supporting documentation through
governed connectors → ground every cited code/amount/policy → **draft** the appeal packet and a
root-cause summary → **suspend at the Denials-Specialist gate** for review and submission.
**Named human gate:** Denials Specialist.

## Systems / connectors (with standards)
- **EHR / FHIR** — Epic / Oracle Health, normalized via Amazon HealthLake (FHIR R4): chart,
  encounter, coverage.
- **Clearinghouse** — Change Healthcare / Availity / Waystar: **X12 837** (claim), **835**
  (remittance/denial), **277** (claim status).
- **Knowledge base** — payer policy / denial-reason corpus for grounding.

## Workforce roles to map in the IdP
`DENIALS_SPECIALIST` (the gate), `DENIALS_MANAGER` (escalation/oversight), `BILLER` (read/assist).
Map these to `custom:hpp_role` in Cognito at engagement time.

## Withheld authority (what it never does)
**Never submits a claim** — `clearinghouse.submit_claim` is **withheld from the agent**. It drafts
the appeal; the Denials Specialist submits. No write to the system of record without the gate.

## Deploy (fixture mode, no PHI)
```
scripts/build_lambdas.sh
scripts/deploy.sh 01-revenue-cycle-denial dev portable native s3://my-cfn-staging/hpp 10.30.0.0/16
```
- Params: `infra/cloudformation/params/01-revenue-cycle-denial.json` · Terraform:
  `terraform apply -var-file=envs/01-revenue-cycle-denial.tfvars`
- VPC CIDR `10.30.0.0/16`. Gateway `portable` (use `agentcore` only where available); runtime
  `native` (Step Functions) or `container` (Fargate).

## Human-gate smoke test
1. Sign in as a seeded `DENIALS_SPECIALIST`.
2. Drive a gated write (draft an appeal packet) and confirm the run **suspends** at the
   Denials-Specialist gate; a HITL item appears.
3. Approve as the specialist → action proceeds, approval written to the **append-only PHI-masked
   audit**.
4. Reject → action does **not** proceed.
5. Attempt `clearinghouse.submit_claim` → gateway **denies by default** (withheld).

## Key regs
HIPAA Privacy/Security, HITECH; payer appeal rules; False Claims Act / OIG exposure on coding
accuracy; CMS-0057-F upstream (denials driven by CO-197 prior-auth gaps).

## Go-live checklist
- [ ] AWS BAA + SI BAA executed; no PHI before both.
- [ ] IdP federated; `DENIALS_SPECIALIST/MANAGER/BILLER` mapped to `custom:hpp_role`.
- [ ] Live connectors validated (Epic/Oracle Health; Change Healthcare/Availity/Waystar; X12
      837/835/277).
- [ ] Guardrail thresholds + grounding corpus tuned to payer policy.
- [ ] CSV/CSA validation signed off; HITL queue SLA ratified.
- [ ] Pen test + HITRUST/SOC 2 evidence assembled; observability + runbooks adopted.
