# AWS-Native Rebuild — 08-contact-center-member-services

AWS-native rebuild of the 08-contact-center-member-services agent. The LangGraph workflow is expressed as an Amazon Step Functions state machine: deterministic nodes are Lambda Task states, Bedrock drafts the narrative artifact in-account, and the human gate is a waitForTaskToken Task that suspends until a verified Member-Services Rep approves — the native equivalent of LangGraph interrupt_before. Substitute ${ENV} at deploy time.

## Workflow → state machine
`intake → verify_member → retrieve → draft_response → compliance_check → [review_gate (waitForTaskToken — Member-Services Rep)] → finalize`

Each pre-gate node is a Lambda Task on `hpp-08-contact-center-member-services-${ENV}-core` (the deterministic core, which calls Bedrock for the narrative draft via the LLM factory). The `review_gate` state is a `waitForTaskToken` Task on `hpp-08-contact-center-member-services-${ENV}-hitl`; the Member-Services Rep approval resumes the machine. `finalize` commits the approved action through the governed connector and writes the PHI-masked audit record.

## Deploy
The state machine is provisioned by `infra/cloudformation/agent-service.yaml` (`AgentId=08-contact-center-member-services`, `DeployMode=native`) or `infra/terraform/modules/agent-service`. Load `stepfunctions/08-contact-center-member-services.asl.json` as the `DefinitionString` (substitute `${ENV}`). The same governed gateway decision and human gate apply as in the container/LangGraph build.
