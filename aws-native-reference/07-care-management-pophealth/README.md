# AWS-Native Rebuild — 07-care-management-pophealth

AWS-native rebuild of the 07-care-management-pophealth agent. The LangGraph workflow is expressed as an Amazon Step Functions state machine: deterministic nodes are Lambda Task states, Bedrock drafts the narrative artifact in-account, and the human gate is a waitForTaskToken Task that suspends until a verified Care Manager approves — the native equivalent of LangGraph interrupt_before. Substitute ${ENV} at deploy time.

## Workflow → state machine
`intake → load_patient → check_consent → identify_gaps → fairness_screen → draft_artifacts → compliance_check → [care_manager_gate (waitForTaskToken — Care Manager)] → finalize`

Each pre-gate node is a Lambda Task on `hpp-07-care-management-pophealth-${ENV}-core` (the deterministic core, which calls Bedrock for the narrative draft via the LLM factory). The `care_manager_gate` state is a `waitForTaskToken` Task on `hpp-07-care-management-pophealth-${ENV}-hitl`; the Care Manager approval resumes the machine. `finalize` commits the approved action through the governed connector and writes the PHI-masked audit record.

## Deploy
The state machine is provisioned by `infra/cloudformation/agent-service.yaml` (`AgentId=07-care-management-pophealth`, `DeployMode=native`) or `infra/terraform/modules/agent-service`. Load `stepfunctions/07-care-management-pophealth.asl.json` as the `DefinitionString` (substitute `${ENV}`). The same governed gateway decision and human gate apply as in the container/LangGraph build.
