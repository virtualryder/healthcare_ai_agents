# HPP AI Agent Suite — Third-Party Risk Management (TPRM) Due-Diligence Packet

> Answers to the questions a hospital or health-plan security and vendor-risk team asks before
> a governed AI agent touches their environment. Scoped to the deployment model where the SI
> deploys and operates the suite **in the customer's own AWS account**. This packet describes
> what the platform enforces in code; it does not assert certifications the suite does not hold.
> Regulatory references are source-class tagged and traced to `../gtm/HPP-DECK-SOURCES.md`.

## A. Deployment model and data residency

The suite is deployed **in the customer's AWS account and Region**, not in an SI-hosted
multi-tenant environment. Inference runs on HIPAA-eligible Amazon Bedrock — a regional AWS
service reached over AWS PrivateLink — under the customer's AWS BAA with
`LLM_PROVIDER=bedrock`. There is **no PHI egress to an external AI API**; traffic to Bedrock
stays on AWS private networking. Each agent is deployed into its own isolated VPC
(CloudFormation CIDRs 10.30–10.37), with a Bedrock VPC interface endpoint (PrivateLink) and
VPC Flow Logs.

## B. Data flows

For a representative agent (Agent 01): a denial record is pulled from the source system via a
governed connector; the agent assembles context and calls Bedrock via PrivateLink (with Guardrails)
to triage and draft a grounded appeal; the draft is queued to the human-review gate; a verified
reviewer (`BILLER` / denials specialist) approves; the consequential action (claim/appeal
submission) is performed by the **human**, not the agent. Every step is written to the
PHI-masked append-only audit trail. PHI is masked at every audit and trace boundary, so it does
not enter logs.

## C. PHI handling and minimum-necessary

- **PHI masker:** HIPAA Safe Harbor identifiers are masked at every audit/trace boundary;
  clinical identifiers needed for the work (NPI, ICD, CPT) are preserved. PHI does not reach
  logs or any external AI API.
- **Minimum-necessary:** enforced by the gateway's least-privilege intersection —
  `permitted(tool) ⇔ tool ∈ AGENT_TOOL_GRANTS[agent] ∩ ROLE_ENTITLEMENTS[user_roles]`. An agent
  can never access more than the human on whose behalf it acts.
- **SUD data:** 42 CFR Part 2 consent gates apply where relevant (Agents 03, 07).

## D. BAA and regulatory posture

An AWS BAA covers Bedrock, HealthLake, and the supporting HIPAA-eligible services. The suite is
designed against HIPAA Privacy/Security Rules + HITECH, 42 CFR Part 2 (SUD), CMS-0057-F `[gov]`,
No Surprises Act `[gov]`, ACA Section 1557 `[gov]`, 21st Century Cures info-blocking, and CMS
expectations for AI in utilization management. Each control is mapped regime→control→AWS service
in the governance materials.

## E. Subprocessors

In the in-customer-account model, the AI inference subprocessor is **AWS** (Amazon Bedrock,
under the customer's BAA). If a customer elects the Anthropic API path (`LLM_PROVIDER=anthropic`)
for non-PHI or development use, Anthropic is the inference processor for that path; the
production HIPAA recommendation is in-account Bedrock with no external egress. The customer's
existing AWS subprocessor posture governs the underlying services.

## F. Encryption

- **At rest:** AWS KMS-managed encryption across DynamoDB, S3 (including the Object Lock WORM
  audit store), and HealthLake.
- **In transit:** TLS for all service calls; the in-account Bedrock endpoint over PrivateLink
  keeps inference traffic on the AWS network.
- **Key management:** customer-controlled KMS keys in the customer's account.

## G. Access control and identity

- Identity via Amazon Cognito or federation to the customer IdP through IAM Identity Center;
  roles carry an `hpp_role` claim that drives entitlements.
- **No standing service accounts:** the gateway issues short-lived, tool-scoped tokens per action.
- **Deny-by-default** authorization; **withheld authorities** (claim submission, coverage
  determination, note signature, recoupment) are not grantable to any agent — they live only with
  human roles (`BILLER`, `UM_MEDICAL_DIRECTOR`, signing clinician).
- Least-privilege IAM roles per the CloudFormation security template.

## H. Audit and logging

The audit trail is **append-only by construction**: DynamoDB denies Update and Delete, and S3
Object Lock provides WORM immutability for the retained record. The PHI masker ensures no Safe
Harbor identifier is written to the trail. Every gated action binds the verified reviewer
identity into the record. This supports the HIPAA Security Rule's audit-control and integrity
requirements with a tamper-evident record. VPC Flow Logs and CloudWatch provide infrastructure
and application observability.

## I. Human-in-the-loop and accountability

High-risk write tools block until a verified reviewer identity is bound into the record —
`interrupt_before=["human_review_gate"]` (LangGraph) or a Step Functions `waitForTaskToken`
task (AWS-native). **Application code cannot bypass the gate.** The agent assists, drafts,
assembles, flags, and recommends; a licensed or credentialed human decides every consequential
action. Accountability for clinical, coverage, and financial decisions remains with the
customer's staff.

## J. AI governance and model-risk

- **Grounding verification** on outputs; **hash-pinned prompt registry** so behavior cannot
  drift silently; **Amazon Bedrock Guardrails** with PHI filters.
- **Eval harness** against golden artifacts, a **red-team** suite, and a **four-fifths fairness
  screen** (aligned with Section 1557 `[gov]`) on UM and risk-stratification outputs; accessibility
  and health-literacy checks on member/patient communications.
- Model/prompt/guardrail/tool-grant changes are governed change events run through these gates
  before production (see `MANAGED-SERVICE-OFFERING.md`).

## K. Breach posture

In the in-customer-account model, the customer's incident-response and breach-notification
processes govern, operating on customer-owned data in the customer's account. The append-only
audit trail and Flow Logs provide forensic evidence. The SI supports investigation per the
managed-service SLA; the SI does not hold or process PHI outside the customer's account in the
production configuration.

## L. SOC 2 / HITRUST roadmap (honest statement)

The accelerator is **not** itself a SOC 2- or HITRUST-certified product, and we do not claim it
is. It is a *Demonstrated + Deployable-by-design* accelerator whose controls are built and
tested (268 automated tests as of 2026-07-10, no API key) and mapped to recognized regimes. Achieving the
tested (268 automated tests as of 2026-07-10, no API key) and mapped to recognized regimes. Achieving the
customer's certification scope — customer computer-system validation (CSV/CSA), live-connector
validation, penetration test, and a HITRUST/SOC 2 assessment of the deployed system — is part of
the production engagement, not a day-one deliverable. We will not overstate this; the maturity
ladder and these limits are documented throughout the suite.

## M. Quick-reference control summary

| Control area | Mechanism |
|---|---|
| Authorization | Deny-by-default + least-privilege intersection (gateway, outside model) |
| Withheld authorities | Claim submit / determination / sign / recoupment never grantable to agents |
| Human gate | Framework-enforced (`interrupt_before` / `waitForTaskToken`), non-bypassable |
| PHI protection | Safe Harbor masker at every boundary; in-account Bedrock under BAA, no egress |
| Audit | Append-only DynamoDB + S3 Object Lock WORM, PHI-masked, identity-bound |
| Tokens | Short-lived, tool-scoped; no standing service accounts |
| AI governance | Grounding, prompt pinning, Guardrails, eval, red team, fairness, accessibility |
| Isolation | Per-agent VPC/KMS/Cognito/audit; customer-controlled keys |
