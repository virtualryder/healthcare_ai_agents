# Terraform & GovCloud status — HPP AI Agent Suite

**Honest status.** CloudFormation/SAM is the **canonical, acceptance-gated** IaC (the Agent 01 golden
path is the one path validated through the acceptance gate — see
[`../evidence/CLEAN-ACCOUNT-ACCEPTANCE.md`](../evidence/CLEAN-ACCOUNT-ACCEPTANCE.md)). The Terraform
under `infra/terraform/` is **substantial and close to parity** for the core architecture, but has
**not** itself been through the acceptance gate. "Parity" here means near-equivalent resource
coverage — not that Terraform is the validated path.

## Coverage: Terraform vs CloudFormation

The Terraform reproduces ~32 AWS resource *types* (of ~40 in the CloudFormation set) across modules
`network / security / data / connectors / gateway / agent-service`:

| Area | CloudFormation | Terraform |
|---|---|---|
| VPC / subnets / NAT / IGW / route tables / flow logs | ✅ | ✅ |
| VPC interface endpoints (PrivateLink) | ✅ | ✅ |
| KMS CMK + alias | ✅ | ✅ |
| DynamoDB audit (append-only) | ✅ | ✅ |
| S3 WORM (Object Lock + encryption + versioning + PAB) | ✅ | ✅ |
| Bedrock Guardrail | ✅ | ✅ |
| MCP gateway: API GW HTTP API + **authorizer + integration + route + stage** | ✅ | ✅ |
| Cognito user pool + client | ✅ | ✅ |
| Step Functions + Lambda (+ permissions) | ✅ | ✅ |
| Security groups, IAM least-privilege roles | ✅ | ✅ |
| **Comprehend Medical opt-in IAM** (PHI engine) | ✅ (gated) | ⚠️ verify present in security module |
| **IdP federation (SAML/OIDC)** addon | ✅ (`idp-federation.yaml`) | ⚠️ not in Terraform |

**Bottom line:** the Terraform is a genuine near-parity reference for the core; the two most recent
additions (Comprehend Medical IAM gating, IdP federation addon) should be reconciled into the
Terraform, and a `terraform validate` / `plan` / `apply` run recorded before calling it validated.

## GovCloud posture

No GovCloud-specific Terraform overlay ships in this repo. HIPAA-eligible services (Bedrock,
Comprehend Medical) are region-parameterized; a GovCloud deployment is engagement work and would use
the portable gateway path (AgentCore Gateway GovCloud availability was still pending as of 2026-05).

## What "done" would require (engagement-owned)

Reconcile the Comprehend-Medical and IdP-federation additions into Terraform; run
`terraform validate` / `plan` / `apply` in a commercial account and record it; deploy remains
**CloudFormation-canonical** (Agent 01 golden path) until Terraform is acceptance-gated.
