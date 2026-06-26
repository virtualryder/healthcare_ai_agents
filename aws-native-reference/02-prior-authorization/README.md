# AWS-Native Rebuild — 02-prior-authorization

AWS-native rebuild of the 02-prior-authorization agent. The LangGraph workflow is expressed as an Amazon Step Functions state machine: deterministic nodes are Lambda Task states, Bedrock drafts the narrative artifact in-account, and the human gate is a waitForTaskToken Task that suspends until a verified PA Nurse approves — the native equivalent of LangGraph interrupt_before. Substitute ${ENV} at deploy time.

## Workflow → state machine
`intake → check_requirement → gather_evidence → evaluate_criteria → assemble_packet → compliance_check → [human_review_gate (waitForTaskToken — PA Nurse)] → finalize`

Each pre-gate node is a Lambda Task on `hpp-02-prior-authorization-${ENV}-core` (the deterministic core, which calls Bedrock for the narrative draft via the LLM factory). The `human_review_gate` state is a `waitForTaskToken` Task on `hpp-02-prior-authorization-${ENV}-hitl`; the PA Nurse approval resumes the machine. `finalize` commits the approved action through the governed connector and writes the PHI-masked audit record.

## Deploy
The state machine is provisioned by `infra/cloudformation/agent-service.yaml` (`AgentId=02-prior-authorization`, `DeployMode=native`) or `infra/terraform/modules/agent-service`. Load `stepfunctions/02-prior-authorization.asl.json` as the `DefinitionString` (substitute `${ENV}`). The same governed gateway decision and human gate apply as in the container/LangGraph build.
