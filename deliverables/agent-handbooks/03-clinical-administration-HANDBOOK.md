# Agent Handbook — 03 Clinical-Administration

Drafts clinical documentation to reduce clinician administrative burden — **draft only, no order
entry**, with a clinician sign-off gate and 42 CFR Part 2 consent. Maturity: Demonstrated +
Deployable-by-design; production-readiness (CSV/CSA, IdP, live connectors, pen test, HITRUST) is
the engagement; AWS BAA precedes any PHI.

## Workflow + human gate
Gather encounter context from the chart → **check 42 CFR Part 2 consent** before touching
sensitive (SUD / behavioral-health) data; escalate if absent → **draft** the clinical note /
summary (`ehr.draft_note`, draft only) → ground every cited fact → **suspend at the clinician
sign-off gate**. **Named human gate:** Clinician sign-off. Ambient documentation has moved
clinician burnout from ~52% to ~39% — but only with the clinician in control.

## Systems / connectors (with standards)
- **EHR / FHIR** — Epic / Oracle Health via Amazon HealthLake (FHIR R4): encounter, observations,
  documents.
- **Consent ledger** — 42 CFR Part 2 / sensitive-scope consent check before disclosure.
- **Knowledge base** — clinical-content corpus for grounding.

## Workforce roles to map in the IdP
`CLINICAL_STAFF` and `PROVIDER` (the sign-off gate). Map to `custom:hpp_role`.

## Withheld authority (what it never does)
**`ehr.draft_note` is draft-only — no order entry, no signed note.** The agent never places an
order, signs a note, or writes to the chart of record. It never discloses or acts on **42 CFR Part
2** data without an explicit consent grant.

## Deploy (fixture mode, no PHI)
```
scripts/build_lambdas.sh
scripts/deploy.sh 03-clinical-administration dev portable native s3://my-cfn-staging/hpp 10.32.0.0/16
```
- Params: `infra/cloudformation/params/03-clinical-administration.json` · Terraform:
  `terraform apply -var-file=envs/03-clinical-administration.tfvars`
- VPC CIDR `10.32.0.0/16`.

## Human-gate smoke test
1. Sign in as a seeded `PROVIDER`.
2. Drive a draft note on a record **without** Part 2 consent → confirm the agent **escalates**
   rather than disclosing.
3. With consent present, draft a note → run **suspends** at the clinician sign-off gate; HITL item
   appears.
4. Sign off → draft proceeds; approval written to the **append-only PHI-masked audit**.
5. Attempt order entry / a signed-note write → **denied by default** (draft-only).

## Key regs
HIPAA Privacy/Security, HITECH; **42 CFR Part 2** (SUD/behavioral-health consent); 21st Century
Cures (information blocking); clinical documentation-integrity policy.

## Go-live checklist
- [ ] AWS BAA + SI BAA executed; no PHI before both.
- [ ] IdP federated; `CLINICAL_STAFF` / `PROVIDER` mapped to `custom:hpp_role`.
- [ ] Live EHR/FHIR connector validated (Epic/Oracle Health via HealthLake).
- [ ] **42 CFR Part 2 consent ledger** wired to the customer's consent source of truth.
- [ ] Guardrail + grounding tuned; CSV/CSA signed off; HITL SLA ratified.
- [ ] Pen test + HITRUST/SOC 2 evidence assembled; observability + runbooks adopted.
