# AWS-Native Rebuild — 01-revenue-cycle-denial

AWS-native rebuild of the 01-revenue-cycle-denial agent. The LangGraph workflow is expressed as an Amazon Step Functions state machine: deterministic nodes are Lambda Task states, Bedrock drafts the narrative artifact in-account, and the human gate is a waitForTaskToken Task that suspends until a verified Denials Specialist approves — the native equivalent of LangGraph interrupt_before. Substitute ${ENV} at deploy time.

## Workflow → state machine
`intake → load_claim → analyze_denial → gather_evidence → draft_appeal → compliance_check → [human_review_gate (waitForTaskToken — Denials Specialist)] → finalize`

Each pre-gate node is a Lambda Task on `hpp-01-revenue-cycle-denial-${ENV}-core` (the deterministic core, which calls Bedrock for the narrative draft via the LLM factory). The `human_review_gate` state is a `waitForTaskToken` Task on `hpp-01-revenue-cycle-denial-${ENV}-hitl`; the Denials Specialist approval resumes the machine. `finalize` commits the approved action through the governed connector and writes the PHI-masked audit record.

## Deploy
The state machine is provisioned by `infra/cloudformation/agent-service.yaml` (`AgentId=01-revenue-cycle-denial`, `DeployMode=native`) or `infra/terraform/modules/agent-service`. Load `stepfunctions/01-revenue-cycle-denial.asl.json` as the `DefinitionString` (substitute `${ENV}`). The same governed gateway decision and human gate apply as in the container/LangGraph build.
