# Agent Handbook — 04 Patient Access

Handles patient-access tasks — eligibility, registration support, and a **deterministic Good Faith
Estimate** under the No Surprises Act — behind an identity gate and an access-rep gate. Maturity:
Demonstrated + Deployable-by-design; production-readiness (CSV/CSA, IdP, live connectors, pen test,
HITRUST) is the engagement; AWS BAA precedes any PHI.

## Workflow + human gate
**Verify patient identity** before any disclosure → check eligibility → compute a **deterministic
Good Faith Estimate** (No Surprises Act) from the actual rate/benefit data (not model-generated
numbers) → assemble registration support → **suspend at the Access-Rep gate**. **Named human
gate:** Access Rep. The GFE is deterministic by design so the estimate is reproducible and
auditable.

## Systems / connectors (with standards)
- **EHR / FHIR** — Epic / Oracle Health via Amazon HealthLake (FHIR R4): patient, coverage,
  scheduling.
- **Payer** — **X12 270/271** (eligibility/benefit); rate/benefit data for the GFE.
- **Identity** — member/patient identity verification before disclosure.

## Workforce roles to map in the IdP
`PATIENT_ACCESS_REP` (the gate). Map to `custom:hpp_role`.

## Withheld authority (what it never does)
The **GFE is deterministic** — the agent does not invent prices; it computes from real
rate/benefit data. It **never discloses patient data without passing the identity gate**, and the
Access Rep owns any consequential registration/financial commitment.

## Deploy (fixture mode, no PHI)
```
scripts/build_lambdas.sh
scripts/deploy.sh 04-patient-access dev portable native s3://my-cfn-staging/hpp 10.33.0.0/16
```
- Params: `infra/cloudformation/params/04-patient-access.json` · Terraform:
  `terraform apply -var-file=envs/04-patient-access.tfvars`
- VPC CIDR `10.33.0.0/16`.

## Human-gate smoke test
1. Attempt a disclosure **before** identity verification → confirm the **identity gate** blocks it.
2. Sign in as a seeded `PATIENT_ACCESS_REP`; verify identity; compute a GFE → confirm the estimate
   is **deterministic** (same inputs → same output).
3. Drive a gated action → run **suspends** at the Access-Rep gate; HITL item appears.
4. Approve → proceeds; approval written to the **append-only PHI-masked audit**. Reject → no
   action.

## Key regs
HIPAA Privacy/Security, HITECH; **No Surprises Act** (Good Faith Estimate); **Section 1557**
(language access / nondiscrimination); identity-proofing best practice.

## Go-live checklist
- [ ] AWS BAA + SI BAA executed; no PHI before both.
- [ ] IdP federated; `PATIENT_ACCESS_REP` mapped to `custom:hpp_role`.
- [ ] Live connectors validated (Epic/Oracle Health; X12 270/271); GFE rate data wired.
- [ ] Identity-proofing flow validated; Section 1557 language-access reviewed.
- [ ] CSV/CSA signed off; HITL SLA ratified; Guardrail tuned.
- [ ] Pen test + HITRUST/SOC 2 evidence assembled; observability + runbooks adopted.
