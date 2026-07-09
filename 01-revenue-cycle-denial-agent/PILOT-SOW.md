# Scoped Pilot SOW — Governed Revenue-Cycle Denials & Appeals Agent on AWS

*Template statement of work for a time-boxed, low-risk pilot proving the governed pattern in the
customer's AWS account. Reference accelerator — not an AWS service, not HITRUST/SOC 2-certified;
HIPAA-eligible ≠ HIPAA-compliant (a signed AWS BAA and customer controls are required). See
[`NOT-CLAIMS.md`](../NOT-CLAIMS.md). Template for scoping, not a signed agreement or legal advice.*

## 1. Objective

Prove, in the provider/payer's AWS account, that an AI agent can **safely** help a denials specialist:
read a denied claim, validate codes and medical necessity, retrieve the relevant coverage policy, and
draft an appeal — **with a qualified denials specialist reviewing and authorizing every submission** and
immutable evidence for every step. Deliberately narrow: **one workflow, one connector path, one approval
path, one evidence report.**

## 2. Duration & shape

**6–10 weeks**: Foundation (1–3) → Governed pilot (3–8) → Evidence & readout (8–10). **Synthetic or
de-identified** claim data only, unless a BAA and PHI handling are separately agreed for the pilot.

## 3. Customer prerequisites (before week 1)

- An AWS account with a signed **AWS BAA**, Amazon Bedrock + the required model in a supported Region.
- An identity provider (Okta / Entra / AD) and the denials-specialist / manager role groups.
- A named **denials specialist** (approves appeal submissions) and a revenue-cycle owner for go/no-go.
- Security/privacy contact (KMS key policy, VPC, Guardrail settings, HIPAA Security Rule review).
- **Data:** **synthetic or de-identified** denied-claim records (835/EOB-shaped). No PHI without the BAA + agreed handling.

## 4. Scope — in

- Deploy the Agent 01 golden path (SAM) into the customer account: MCP gateway, Step Functions workflow
  with the `waitForTaskToken` human gate, append-only + S3 Object-Lock audit, PHI masking, token budget,
  Bedrock + Guardrails over PrivateLink.
- **One connector path:** the **tier-1 documented X12 835 scaffold** OR a **tier-2 local HTTP stand-in**
  shaped like the customer's clearinghouse/PAS. (Production 835 feed / Epic = out of scope, §5.)
- Wire the customer IdP + the denials roles; exercise the human-approval gate on every appeal submission.
- Run the governed workflow end-to-end on synthetic claims; produce the immutable audit evidence.
- Run the 10-point negative demo (`make neg-demo`) in the customer account as an acceptance gate.

## 5. Scope — out (explicitly)

- **Production connector to a payer/clearinghouse 835 feed, Epic/ADT, or HealthLake PHI (tier-4)** —
  separate SOW under the BAA.
- Real claim/appeal submission to a payer or clearinghouse.
- HITRUST/SOC 2, penetration test, production monitoring, DR, operations.
- **Agents 02–08** (not clean-account-gated; a later phase).

## 6. Success metrics (agreed before week 3)

- **Governance:** 10/10 negative-demo refusals enforced; no PHI in any audit record (fail-closed masking).
- **Human authority:** every appeal submission blocks at the specialist gate; the agent never submits a claim.
- **Quality (illustrative, to be baselined):** appeal-draft acceptance rate by reviewers; recoverable-denial identification vs. the manual baseline.
- **Evidence:** a complete append-only audit trail for every pilot claim, exported as the evidence pack.

## 7. Security gates (must pass to proceed to readout)

Signed BAA; deny-by-default gateway live; bound single-use SoD approvals; scoped short-lived tokens;
fail-closed PHI masking; append-only + WORM audit; Bedrock reached only over PrivateLink with no PHI
egress to external AI APIs. Reviewed against [`ASSURANCE-PACKET.md`](ASSURANCE-PACKET.md),
[`docs/compliance.md`](docs/compliance.md), and [`../docs/THREAT-MODEL.md`](../docs/THREAT-MODEL.md).

## 8. Deployment path

Canonical: the per-agent **SAM golden path** — `sam build && sam deploy` + smoke test + teardown.
Runbook: [`docs/aws-deployment-guide.md`](docs/aws-deployment-guide.md). Prerequisites:
[`../docs/AWS-ACCOUNT-PREREQUISITES.md`](../docs/AWS-ACCOUNT-PREREQUISITES.md).

## 9. Deliverables

1. Deployed governed Agent 01 golden path in the customer account.
2. Evidence pack: clean-account acceptance, the negative-demo result, and the per-claim audit export.
3. A go/no-go readout with the success-metric results and a scoped path to production (835/Epic connector under BAA, HITRUST, IdP, monitoring).

## 10. Go / no-go criteria

**Go** if: BAA in place, all security gates pass, 10/10 refusals enforced, PHI-leak = 0, the specialist
gate held on every submission, and the quality metrics meet the agreed thresholds. **No-go / iterate**
if any security gate fails or the human-authority boundary is not demonstrably enforced.

## 11. Shared responsibility

Per [`ASSURANCE-PACKET.md` §8](ASSURANCE-PACKET.md) and
[`../docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`](../docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md).
The accelerator provides the governed control plane; the customer owns the BAA, identity, production
connectors, validation, and operations.
