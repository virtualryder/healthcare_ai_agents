# _shared — AWS-native platform notes

All eight native rebuilds share the same platform contract as the container/LangGraph build:

- **Core Lambda** (`hpp-<agent>-<env>-core`) runs the deterministic nodes and calls Amazon Bedrock (in-account, under the AWS BAA) for the narrative draft via `hpp_agent_platform.llm_factory`. Every system-of-record call still flows through the MCP authorization gateway (deny-by-default + least-privilege intersection + tool-scoped tokens).
- **HITL Lambda** (`hpp-<agent>-<env>-hitl`) is the `waitForTaskToken` target: it records the pending review in the HITL DynamoDB table and returns the token; a verified reviewer's approval (bound with their identity) resumes the state machine. High-risk writes cannot execute before this.
- **Audit**: every transition writes a PHI-masked record to the append-only audit DynamoDB table; finalized snapshots land in the S3 Object Lock (WORM) bucket.
- **Withheld authorities** are enforced in the gateway exactly as in the LangGraph build — the state machine cannot reach a tool the agent is not granted (no claim submission, no UM determination).

The `.asl.json` files are reference definitions; `${ENV}` is substituted at deploy time by `infra/cloudformation/agent-service.yaml` or the Terraform `agent-service` module.
