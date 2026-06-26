# AWS-Native Rebuild — 03-clinical-administration

AWS-native rebuild of the 03-clinical-administration agent. The LangGraph workflow is expressed as an Amazon Step Functions state machine: deterministic nodes are Lambda Task states, Bedrock drafts the narrative artifact in-account, and the human gate is a waitForTaskToken Task that suspends until a verified Clinician approves — the native equivalent of LangGraph interrupt_before. Substitute ${ENV} at deploy time.

## Workflow → state machine
`intake → load_chart → check_consent → produce_artifact → compliance_check → [clinician_review_gate (waitForTaskToken — Clinician)] → finalize`

Each pre-gate node is a Lambda Task on `hpp-03-clinical-administration-${ENV}-core` (the deterministic core, which calls Bedrock for the narrative draft via the LLM factory). The `clinician_review_gate` state is a `waitForTaskToken` Task on `hpp-03-clinical-administration-${ENV}-hitl`; the Clinician approval resumes the machine. `finalize` commits the approved action through the governed connector and writes the PHI-masked audit record.

## Deploy
The state machine is provisioned by `infra/cloudformation/agent-service.yaml` (`AgentId=03-clinical-administration`, `DeployMode=native`) or `infra/terraform/modules/agent-service`. Load `stepfunctions/03-clinical-administration.asl.json` as the `DefinitionString` (substitute `${ENV}`). The same governed gateway decision and human gate apply as in the container/LangGraph build.
