# Agent Handbook — 05 Utilization Management

The payer-side wedge. Summarizes a UM request against medical-necessity criteria and runs a
fairness screen — but **issuing the determination is withheld from every agent**, and an adverse
recommendation is **forwarded to the medical director, never auto-denied**. Maturity: Demonstrated
+ Deployable-by-design; production-readiness (CSV/CSA, IdP, live connectors, pen test, HITRUST) is
the engagement; AWS BAA precedes any PHI.

## Workflow + human gate
Receive a UM/medical-necessity request → assemble clinical evidence → summarize against **MCG /
InterQual** criteria → run the **four-fifths fairness screen** on the recommendation → **suspend at
the Medical-Director gate**. An **adverse** recommendation is **forwarded** to the medical director,
**never auto-denied**. **Named human gate:** Medical Director.

## Systems / connectors (with standards)
- **EHR / FHIR** — Epic / Oracle Health via Amazon HealthLake (FHIR R4): clinical evidence.
- **Criteria** — **MCG / InterQual** medical-necessity criteria for grounding.
- **Payer** — **Da Vinci** (CRD/DTR/PAS); **X12 278** for the UM transaction.

## Workforce roles to map in the IdP
`UM_NURSE` (review/assemble) and `UM_MEDICAL_DIRECTOR` (the determination gate). Map to
`custom:hpp_role`.

## Withheld authority (what it never does)
**`payer.issue_determination` is WITHHELD from ALL agents.** No agent issues a coverage/UM
determination. An adverse recommendation is **forwarded** to the Medical Director; it is **never
auto-denied**. The four-fifths fairness screen runs on every flag/rank.

## Deploy (fixture mode, no PHI)
```
scripts/build_lambdas.sh
scripts/deploy.sh 05-utilization-management dev portable native s3://my-cfn-staging/hpp 10.34.0.0/16
```
- Params: `infra/cloudformation/params/05-utilization-management.json` · Terraform:
  `terraform apply -var-file=envs/05-utilization-management.tfvars`
- VPC CIDR `10.34.0.0/16`.

## Human-gate smoke test
1. Sign in as a seeded `UM_NURSE`; drive a UM summary with an **adverse** recommendation → confirm
   it is **forwarded** to the Medical Director and **suspends** at that gate (never auto-denied).
2. Confirm the **four-fifths fairness screen** ran on the recommendation.
3. As `UM_MEDICAL_DIRECTOR`, approve → proceeds; approval written to the **append-only PHI-masked
   audit**. Reject → no determination issued.
4. Attempt `payer.issue_determination` from any agent path → **denied by default** (withheld from
   all).

## Key regs
HIPAA Privacy/Security, HITECH; **CMS AI-in-UM guidance** (no automated denials of medically
necessary care); **CMS-0057-F**; Section 1557 (nondiscrimination — the fairness screen); plan
medical policy.

## Go-live checklist
- [ ] AWS BAA + SI BAA executed; no PHI before both.
- [ ] IdP federated; `UM_NURSE` / `UM_MEDICAL_DIRECTOR` mapped to `custom:hpp_role`.
- [ ] MCG/InterQual criteria + FHIR connectors validated; X12 278 path confirmed.
- [ ] **Four-fifths fairness screen** validated on customer data; adverse-action routing confirmed.
- [ ] CSV/CSA signed off; HITL SLA ratified; Guardrail (unauthorized-determination denied topic)
      confirmed.
- [ ] Pen test + HITRUST/SOC 2 evidence assembled; observability + runbooks adopted.
