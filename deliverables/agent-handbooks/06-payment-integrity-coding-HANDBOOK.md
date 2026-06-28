# Agent Handbook — 06 Payment Integrity & Coding

Reviews claims and coding for payment-integrity issues and **flags only** — no recoupment, no
submission. Maturity: Demonstrated + Deployable-by-design; production-readiness (CSV/CSA, IdP,
live connectors, pen test, HITRUST) is the engagement; AWS BAA precedes any PHI.

## Workflow + human gate
Ingest a claim / coded encounter → run edit checks (NCCI / MUE, DRG validation) against the chart
→ ground each finding to the supporting evidence → **flag** suspected over/under-coding or
integrity issues → **suspend at the Reviewer gate**. **Named human gate:** Reviewer. CMS reports
$28.8B of $37.4B improper-payment exposure in the relevant programs — the value is accurate
flagging, not automated action.

## Systems / connectors (with standards)
- **EHR / FHIR** — Epic / Oracle Health via Amazon HealthLake (FHIR R4): chart evidence.
- **Encoder** — **NCCI / MUE** edits, **DRG** validation references for grounding.
- **Clearinghouse** — **X12 837 / 835** for the claim and remittance context.

## Workforce roles to map in the IdP
`CODING_SPECIALIST` (the Reviewer gate). Map to `custom:hpp_role`.

## Withheld authority (what it never does)
**Flags only — no recoupment, no claim submission, no code change to the record.** The agent
surfaces findings with evidence; the Reviewer decides whether to act. No autonomous financial or
coding action.

## Deploy (fixture mode, no PHI)
```
scripts/build_lambdas.sh
scripts/deploy.sh 06-payment-integrity-coding dev portable native s3://my-cfn-staging/hpp 10.35.0.0/16
```
- Params: `infra/cloudformation/params/06-payment-integrity-coding.json` · Terraform:
  `terraform apply -var-file=envs/06-payment-integrity-coding.tfvars`
- VPC CIDR `10.35.0.0/16`.

## Human-gate smoke test
1. Sign in as a seeded `CODING_SPECIALIST`.
2. Drive a review that produces a coding flag → confirm the run **suspends** at the Reviewer gate;
   HITL item appears with grounded evidence.
3. Approve a flag → recorded to the **append-only PHI-masked audit**; reject → dropped.
4. Attempt any recoupment / submit / code-change tool → **denied by default** (flags-only).

## Key regs
HIPAA Privacy/Security, HITECH; **False Claims Act / OIG** (coding integrity); CMS improper-payment
/ RADV rules; NCCI/MUE and DRG coding policy.

## Go-live checklist
- [ ] AWS BAA + SI BAA executed; no PHI before both.
- [ ] IdP federated; `CODING_SPECIALIST` mapped to `custom:hpp_role`.
- [ ] NCCI/MUE + DRG references and FHIR/clearinghouse (X12 837/835) connectors validated.
- [ ] Grounding tuned so every flag traces to chart/edit evidence; CSV/CSA signed off; HITL SLA
      ratified.
- [ ] Pen test + HITRUST/SOC 2 evidence assembled; observability + runbooks adopted.
