# AWS-Native Rebuild — 04-patient-access

AWS-native rebuild of the 04-patient-access agent. The LangGraph workflow is expressed as an Amazon Step Functions state machine: deterministic nodes are Lambda Task states, Bedrock drafts the narrative artifact in-account, and the human gate is a waitForTaskToken Task that suspends until a verified Access Rep approves — the native equivalent of LangGraph interrupt_before. Substitute ${ENV} at deploy time.

## Workflow → state machine
`intake → verify_identity → check_eligibility → estimate_cost → get_availability → prepare_summary → compliance_check → [human_review_gate (waitForTaskToken — Access Rep)] → finalize`

Each pre-gate node is a Lambda Task on `hpp-04-patient-access-${ENV}-core` (the deterministic core, which calls Bedrock for the narrative draft via the LLM factory). The `human_review_gate` state is a `waitForTaskToken` Task on `hpp-04-patient-access-${ENV}-hitl`; the Access Rep approval resumes the machine. `finalize` commits the approved action through the governed connector and writes the PHI-masked audit record.

## Deploy
The state machine is provisioned by `infra/cloudformation/agent-service.yaml` (`AgentId=04-patient-access`, `DeployMode=native`) or `infra/terraform/modules/agent-service`. Load `stepfunctions/04-patient-access.asl.json` as the `DefinitionString` (substitute `${ENV}`). The same governed gateway decision and human gate apply as in the container/LangGraph build.
