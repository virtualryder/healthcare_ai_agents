# AWS-Native Rebuild — 05-utilization-management

AWS-native rebuild of the 05-utilization-management agent. The LangGraph workflow is expressed as an Amazon Step Functions state machine: deterministic nodes are Lambda Task states, Bedrock drafts the narrative artifact in-account, and the human gate is a waitForTaskToken Task that suspends until a verified Medical Director approves — the native equivalent of LangGraph interrupt_before. Substitute ${ENV} at deploy time.

## Workflow → state machine
`intake → gather_clinical → evaluate_criteria → fairness_screen → draft_recommendation → compliance_check → [medical_director_gate (waitForTaskToken — Medical Director)] → finalize`

Each pre-gate node is a Lambda Task on `hpp-05-utilization-management-${ENV}-core` (the deterministic core, which calls Bedrock for the narrative draft via the LLM factory). The `medical_director_gate` state is a `waitForTaskToken` Task on `hpp-05-utilization-management-${ENV}-hitl`; the Medical Director approval resumes the machine. `finalize` commits the approved action through the governed connector and writes the PHI-masked audit record.

## Deploy
The state machine is provisioned by `infra/cloudformation/agent-service.yaml` (`AgentId=05-utilization-management`, `DeployMode=native`) or `infra/terraform/modules/agent-service`. Load `stepfunctions/05-utilization-management.asl.json` as the `DefinitionString` (substitute `${ENV}`). The same governed gateway decision and human gate apply as in the container/LangGraph build.
