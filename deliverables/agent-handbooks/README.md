# Agent Handbooks — Index

One handbook per agent in the HPP AI Agent Suite ("HCOS"). Each is a deployment-and-operations
deliverable for the team standing up that agent: the workflow and its named human gate, the
systems/connectors and their X12/FHIR standards, the workforce roles to map in the IdP, the
withheld authority (what the agent never does), a step-by-step `scripts/deploy.sh` deploy with the
agent's VPC CIDR, a human-gate smoke test, the key regulations, and a go-live checklist.

**Maturity stance (every agent):** Demonstrated + Deployable-by-design today (196 tests as of
2026-07-10, no API key). Production-readiness — CSV/CSA validation, IdP federation, live connectors,
penetration test, HITRUST/SOC 2 — is the **engagement**. An executed **AWS BAA precedes any PHI**;
until then the suite runs in **fixture mode**.

## Handbooks

| # | Agent | Named human gate | Withheld authority | VPC CIDR |
|---|---|---|---|---|
| 01 | [Revenue-Cycle & Denial](01-revenue-cycle-denial-HANDBOOK.md) | Denials Specialist | Cannot submit a claim (`clearinghouse.submit_claim` withheld) | `10.30.0.0/16` |
| 02 | [Prior-Authorization](02-prior-authorization-HANDBOOK.md) | PA Nurse | Submits the PA; coverage determination is the payer's | `10.31.0.0/16` |
| 03 | [Clinical-Administration](03-clinical-administration-HANDBOOK.md) | Clinician sign-off | `ehr.draft_note` draft-only, no order entry; 42 CFR Part 2 consent | `10.32.0.0/16` |
| 04 | [Patient Access](04-patient-access-HANDBOOK.md) | Access Rep | Deterministic GFE (No Surprises Act); identity gate | `10.33.0.0/16` |
| 05 | [Utilization Management](05-utilization-management-HANDBOOK.md) | Medical Director | `payer.issue_determination` withheld from ALL agents; adverse rec forwarded, never auto-denied; fairness screen | `10.34.0.0/16` |
| 06 | [Payment Integrity & Coding](06-payment-integrity-coding-HANDBOOK.md) | Reviewer | Flags only — no recoupment/submit | `10.35.0.0/16` |
| 07 | [Care Management & Pop Health](07-care-management-pophealth-HANDBOOK.md) | Care Manager | Gated care-plan write; risk-strat fairness screen; 42 CFR Part 2 consent | `10.36.0.0/16` |
| 08 | [Contact Center / Member Services](08-contact-center-member-services-HANDBOOK.md) | Member-Services Rep | Cannot submit an appeal; identity gate before disclosure; Amazon Connect | `10.37.0.0/16` |

## Deploy signature (all agents)
```
scripts/deploy.sh <AgentId> <env> <portable|agentcore> <native|container> s3://bucket/prefix <VpcCidr>
```
Per-agent params: `infra/cloudformation/params/<agent>.json` · Terraform:
`terraform apply -var-file=envs/<agent>.tfvars`.

## Related
- Pre-flight: `docs/AWS-ACCOUNT-PREREQUISITES.md` · Deploy path: `docs/DEPLOY-QUICKSTART.md`
- Deployment stances: `docs/DEPLOYMENT-MODELS.md`
- Security review: `gtm/SELLER-SA-FIELD-GUIDE.md` (§ CISO checklist), `SECURITY.md`,
  `docs/THREAT-MODEL.md`, `docs/NIST-800-53-CONTROL-MATRIX.md`, `docs/OWASP-LLM-ATLAS-MAPPING.md`
- Platform / orchestration: `ENTERPRISE-PLATFORM.md`, `gtm/HPP-PLATFORM-GTM-STORY.md`
- Future agents: `docs/FUTURE-USE-CASES.md`
- Sourced statistics: `gtm/HPP-DECK-SOURCES.md`, `SOURCES.md`
