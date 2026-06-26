# Deploy Quickstart — Empty Account to Running Governed Agent

This is the copy-paste path from an empty AWS account to a running, governed HPP agent with
a working human gate. It deploys the real CloudFormation stacks via the shipped scripts. The
suite is Deployable-by-design; this quickstart stands up the platform in **fixture mode** —
production hardening (live connectors, IdP integration, validation, pen test) is the
engagement and is flagged in the go-live checklist.

> **Prove it on a laptop first.** Before touching AWS, run the no-API-key demo and the full
> test suite locally — see [`../GETTING-STARTED.md`](../GETTING-STARTED.md) Steps 1–2. That
> de-risks the deploy: you confirm the governance controls and the human gate before any
> infrastructure exists.

## 0. Prerequisites

- **AWS account** with admin (or sufficient) permissions and the AWS CLI configured.
- **Amazon Bedrock model access** enabled in your Region for the chosen foundation model
  (in-account inference keeps PHI under the AWS BAA — no external egress).
- **AWS BAA executed** with AWS before any PHI touches the system. No PHI in fixture mode;
  the BAA must be in place before going live.
- **KMS** — the security stack provisions a customer-managed CMK; ensure you can create KMS
  keys in the Region.
- **Amazon Cognito** — the security stack creates a user pool with the `custom:hpp_role`
  claim; have your role taxonomy ready (mapped to your IdP at engagement time).
- **Service quotas** — confirm headroom for Lambda concurrency, Step Functions, DynamoDB,
  and Bedrock TPM/RPM in the target Region; raise quotas before load testing.
- **An S3 bucket** to stage the nested CloudFormation templates.

## 1. Build the Lambda packages

```
scripts/build_lambdas.sh
```

This packages the connector and service Lambdas for deployment.

## 2. Deploy the stack

```
scripts/deploy.sh <AgentId> <env> <portable|agentcore> <native|container> s3://bucket/prefix <VpcCidr>
```

- **`<AgentId>`** — one of `01-revenue-cycle-denial` … `08-contact-center-member-services`.
- **`<env>`** — e.g. `dev`, `stage`, `prod`.
- **`<portable|agentcore>`** — gateway mode: `portable` (API Gateway + Cognito + STS) or
  `agentcore` (Bedrock AgentCore Gateway/Identity).
- **`<native|container>`** — deploy mode for the agent service.
- **`s3://bucket/prefix`** — where nested templates are staged (required).
- **`<VpcCidr>`** — per-agent VPC CIDR (defaults `10.30.0.0/16` … `10.37.0.0/16`; see
  `infra/cloudformation/params/<agent>.json`).

Example (flagship agent, dev):

```
scripts/deploy.sh 01-revenue-cycle-denial dev portable native s3://my-cfn-staging/hpp 10.30.0.0/16
```

The script stages templates, deploys `quickstart.yaml` (the master stack that nests
network / security / data / connectors / gateway / agent-service), and prints stack outputs.
What gets created:
- **Security stack:** KMS CMK, **Bedrock Guardrail** (PHI filters + unauthorized-
  determination denied topic), **Cognito pool** with `custom:hpp_role`, least-privilege
  agent role.
- **Data stack:** append-only **audit DynamoDB** (PITR, KMS), **HITL table**, **WORM S3**
  (Object Lock COMPLIANCE, 7-year default).
- **Network / connectors / gateway / agent-service** stacks per the chosen modes.

Per-agent parameter files live at `infra/cloudformation/params/<agent>.json` — use them to
pin `AgentId`, `Environment`, `GatewayMode`, and `DeployMode`.

## 3. Create / activate the agent

Confirm the stack outputs (gateway endpoint, audit/HITL table names, Guardrail ID). The
agent service is deployed by the stack; register the agent against the gateway and confirm
it loads its hash-pinned prompt from the prompt registry. Seed a Cognito user with the
appropriate `custom:hpp_role` for the smoke test.

## 4. Human-gate smoke test

Drive one high-risk action end to end and confirm the gate holds:

1. Sign in as the seeded reviewer role.
2. Invoke the agent to perform a gated write (e.g., for agent 01, draft a denial work
   product — recall the agent **cannot submit a claim**).
3. Confirm the execution **suspends** at the named human gate (LangGraph `interrupt_before`
   / Step Functions `waitForTaskToken`) and an item appears in the HITL table.
4. Approve as the named reviewer; confirm the action proceeds and the approval is written
   to the **append-only audit** (PHI-masked).
5. Repeat with a **rejection** and confirm the action does **not** proceed.
6. Attempt an out-of-scope tool call and confirm the gateway **denies by default**.

## 5. Go-live checklist (engagement work)

- [ ] AWS BAA executed; SI BAA executed; no PHI used before both are in place.
- [ ] Enterprise **IdP integrated** with Cognito; `custom:hpp_role` mapped to real roles.
- [ ] **Live connectors** validated against the real EHR / clearinghouse / payer portal /
      FHIR APIs (move off fixture mode).
- [ ] **CSV/CSA validation** plan executed and signed off by the Healthcare Org.
- [ ] **Bedrock Guardrail** thresholds and denied topics tuned to customer policy.
- [ ] **Penetration test** and red-team review completed.
- [ ] **HITRUST/SOC 2** evidence package assembled from the control mappings.
- [ ] Runbooks adopted: incident response, DR (RPO/RTO ratified), HITL queue SLAs,
      model-degradation change control.
- [ ] Observability wired to the customer's monitoring/alerting stack.

## Troubleshooting
- **`cfn-lint` or deploy fails on a resource** — confirm the Region supports the resource (Bedrock
  Guardrails, AgentCore). For Regions without AgentCore, use `GatewayMode=portable` (the default).
- **Bedrock AccessDenied** — enable model access for the chosen model in the Bedrock console for
  the Region, and confirm the agent role allows `bedrock:InvokeModel` / `bedrock:ApplyGuardrail`.
- **CIDR overlap deploying multiple agents** — give each agent a distinct `VpcCidr`
  (`10.30.0.0/16` … `10.37.0.0/16`; see `infra/cloudformation/params/<agent>.json`).
- **Human gate never resumes** — confirm the HITL Lambda returns the task token and the reviewer
  identity is bound; check the HITL DynamoDB table and the Step Functions execution.
- **Want to undo everything** — delete the `hpp-<agent>-<env>` CloudFormation stack (or
  `terraform destroy -var-file=envs/<agent>.tfvars`). Note the WORM bucket retains objects until
  the Object Lock retention elapses — by design.
