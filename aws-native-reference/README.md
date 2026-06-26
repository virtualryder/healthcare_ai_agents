# AWS-Native Reference — Step Functions Rebuilds

Each agent's LangGraph workflow has a native Amazon Step Functions equivalent: deterministic nodes as Lambda Task states, Bedrock drafting in-account, and a **`waitForTaskToken` human gate** that suspends until a verified reviewer approves — the native equivalent of LangGraph `interrupt_before`. The state machine *is* the agent; the same governed gateway decision, PHI-masked audit, and withheld authorities apply.

| Agent | Human gate (waitForTaskToken) | ASL |
|---|---|---|
| 01-revenue-cycle-denial | Denials Specialist | `01-revenue-cycle-denial/stepfunctions/01-revenue-cycle-denial.asl.json` |
| 02-prior-authorization | PA Nurse | `02-prior-authorization/stepfunctions/02-prior-authorization.asl.json` |
| 03-clinical-administration | Clinician | `03-clinical-administration/stepfunctions/03-clinical-administration.asl.json` |
| 04-patient-access | Access Rep | `04-patient-access/stepfunctions/04-patient-access.asl.json` |
| 05-utilization-management | Medical Director | `05-utilization-management/stepfunctions/05-utilization-management.asl.json` |
| 06-payment-integrity-coding | Payment-Integrity Reviewer | `06-payment-integrity-coding/stepfunctions/06-payment-integrity-coding.asl.json` |
| 07-care-management-pophealth | Care Manager | `07-care-management-pophealth/stepfunctions/07-care-management-pophealth.asl.json` |
| 08-contact-center-member-services | Member-Services Rep | `08-contact-center-member-services/stepfunctions/08-contact-center-member-services.asl.json` |

`container` deploy mode lifts the LangGraph agent unchanged onto ECS Fargate / AgentCore Runtime (ARM64, `/invocations`+`/ping`); `native` deploy mode runs these state machines. Pick per agent with `DeployMode` in `infra/`. See `_shared/README.md` for the platform contract.
