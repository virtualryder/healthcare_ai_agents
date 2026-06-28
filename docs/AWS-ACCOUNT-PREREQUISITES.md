# AWS Account Prerequisites — Pre-Flight Checklist

Run this checklist **before** `scripts/deploy.sh` on a fresh AWS account. It complements
`docs/DEPLOY-QUICKSTART.md` (the copy-paste deploy path) and `scripts/deploy.sh` (the deploy
script). Nothing here uses PHI; the **AWS BAA must be executed before any PHI** touches the
system, and the suite runs in **fixture mode** until live connectors and the BAA are in place.

## 1. Legal — AWS BAA
- [ ] **AWS Business Associate Agreement (BAA) executed** with AWS (via AWS Artifact /
      Organizations). Required before any PHI. In-account Bedrock under the BAA is what keeps PHI
      from egressing to an external model. No BAA → fixture mode only.
- [ ] SI / partner BAA executed with the customer (separate from the AWS BAA).

## 2. Amazon Bedrock — model access in-Region
- [ ] **Bedrock model access enabled** for the chosen foundation model **in your target Region**
      (Bedrock console → Model access). In-account inference keeps PHI under the BAA — no external
      egress.
- [ ] Agent role permitted `bedrock:InvokeModel` and `bedrock:ApplyGuardrail` (provisioned by the
      security stack; confirm not denied by an SCP).
- [ ] **Bedrock Guardrails** available in-Region (PHI filters + the unauthorized-determination
      denied topic are created by the security stack).

## 3. Service quotas (raise before load testing)
Confirm headroom in the **target Region** — defaults are often too low for a pilot under load:
- [ ] **Lambda** — concurrent-execution limit (connector + service + HITL Lambdas).
- [ ] **Step Functions** — state-machine executions / state-transition rate (native runtime + the
      `waitForTaskToken` human gate).
- [ ] **DynamoDB** — table/throughput for the append-only audit and HITL tables.
- [ ] **Amazon Bedrock** — model **TPM/RPM** (tokens- and requests-per-minute) for the chosen
      model; this is the most common load-test bottleneck.
- [ ] Raise quotas via Service Quotas **before** any load or pilot testing.

## 4. KMS
- [ ] Ability to **create customer-managed CMKs** in the Region (the security stack provisions a
      per-environment CMK for DynamoDB, S3, and signing material). Confirm no SCP blocks
      `kms:CreateKey`.

## 5. Identity — Cognito / IdP
- [ ] Ability to create a **Amazon Cognito** user pool (the security stack creates one with the
      `custom:hpp_role` claim).
- [ ] **Role taxonomy ready** to map to your enterprise **IdP** at engagement time (e.g.,
      `DENIALS_SPECIALIST`, `PA_COORDINATOR`, `UM_MEDICAL_DIRECTOR`, …). The IdP federation and the
      entitlement source of truth are **customer-owned**.

## 6. S3 staging bucket
- [ ] An **S3 bucket** to stage the nested CloudFormation templates (the `s3://bucket/prefix`
      argument to `scripts/deploy.sh`). Same Region as the deploy; deployer can `s3:PutObject` and
      CloudFormation can read the staged templates.

## 7. AgentCore Region check (else portable)
- [ ] Check whether **Amazon Bedrock AgentCore Gateway/Identity** is available in your target
      Region.
  - Available → you may deploy with `GatewayMode=agentcore`.
  - **Not available → use `GatewayMode=portable`** (API Gateway + Cognito + STS — the default and
    works in every Region). The deploy falls back to portable when AgentCore is absent.

## 8. Detective controls baseline
Enable the account-level baseline before go-live (customer-owned; the matrix marks these
Configurable in `docs/NIST-800-53-CONTROL-MATRIX.md` SI-4):
- [ ] **CloudTrail** — management + data events to a protected bucket.
- [ ] **Amazon GuardDuty** — enabled in the Region.
- [ ] **AWS Security Hub** — enabled with the relevant standards.
- [ ] **AWS Config** — recording, with conformance packs for the controls you must evidence.

## 9. Build & deploy (then hand to the quickstart)
- [ ] AWS CLI configured with sufficient permissions (admin or scoped deploy role).
- [ ] Build the Lambda packages: `scripts/build_lambdas.sh`.
- [ ] Deploy:
      `scripts/deploy.sh <AgentId> <env> <portable|agentcore> <native|container> s3://bucket/prefix <VpcCidr>`
      — e.g. `scripts/deploy.sh 01-revenue-cycle-denial dev portable native s3://my-cfn-staging/hpp 10.30.0.0/16`.
- [ ] Continue with `docs/DEPLOY-QUICKSTART.md` §3–§5 (activate the agent, run the human-gate smoke
      test, work the go-live checklist).

> Distinct **VPC CIDRs** per agent (`10.30.0.0/16` … `10.37.0.0/16`) avoid overlap when deploying
> multiple agents — see `docs/DEPLOYMENT-MODELS.md`.
