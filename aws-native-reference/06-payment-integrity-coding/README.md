# AWS-Native Rebuild — 06-payment-integrity-coding

AWS-native rebuild of the 06-payment-integrity-coding agent. The LangGraph workflow is expressed as an Amazon Step Functions state machine: deterministic nodes are Lambda Task states, Bedrock drafts the narrative artifact in-account, and the human gate is a waitForTaskToken Task that suspends until a verified Payment-Integrity Reviewer approves — the native equivalent of LangGraph interrupt_before. Substitute ${ENV} at deploy time.

## Workflow → state machine
`intake → load_claim → analyze_coding → detect_issues → draft_finding → compliance_check → [review_gate (waitForTaskToken — Payment-Integrity Reviewer)] → finalize`

Each pre-gate node is a Lambda Task on `hpp-06-payment-integrity-coding-${ENV}-core` (the deterministic core, which calls Bedrock for the narrative draft via the LLM factory). The `review_gate` state is a `waitForTaskToken` Task on `hpp-06-payment-integrity-coding-${ENV}-hitl`; the Payment-Integrity Reviewer approval resumes the machine. `finalize` commits the approved action through the governed connector and writes the PHI-masked audit record.

## Deploy
The state machine is provisioned by `infra/cloudformation/agent-service.yaml` (`AgentId=06-payment-integrity-coding`, `DeployMode=native`) or `infra/terraform/modules/agent-service`. Load `stepfunctions/06-payment-integrity-coding.asl.json` as the `DefinitionString` (substitute `${ENV}`). The same governed gateway decision and human gate apply as in the container/LangGraph build.
