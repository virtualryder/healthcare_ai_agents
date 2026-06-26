# Shared Responsibility Matrix — HPP AI Agent Suite

Security and compliance for a governed healthcare AI agent are shared across three parties:
**AWS** (the cloud provider, under the AWS Shared Responsibility Model and the AWS BAA), the
**SI** (the systems integrator delivering and configuring the suite — i.e., this
accelerator and the engagement team), and the **Healthcare Org** (the covered entity or
health plan that owns the data, the clinical/coverage decisions, and the regulatory
relationship). The line that runs through every row: AWS secures the cloud; the SI
configures the governed platform; the Healthcare Org owns accountability for care, coverage,
and the patient relationship.

Maturity legend for the SI column: **I** = Implemented in the accelerator, **C** =
Configurable per customer at engagement, **—** = not applicable.

| Control / area | AWS | SI (accelerator + engagement) | Healthcare Org |
|---|---|---|---|
| **HIPAA Security Rule** (access, audit, integrity, encryption) | Secure HIPAA-eligible services; KMS, infra controls | Deny-by-default gateway, PHI-masked append-only audit (DynamoDB deny U/D + PITR, S3 WORM), scoped tokens **(I/C)** | Designate Security Officer; risk analysis; sanction policy; accept residual risk |
| **HIPAA Privacy Rule** (minimum necessary) | — | Least-privilege intersection (agent grant ∩ user entitlement); per-tool scoping **(I)** | Define entitlements/roles; notice of privacy practices; authorizations |
| **AWS BAA** | Offer & sign the BAA; keep services BAA-eligible | Architect PHI to stay in-account (in-account Bedrock, VPC endpoints, no egress) **(C)** | **Execute the BAA with AWS**; execute a BAA with the SI as business associate |
| **Validation (CSV / CSA)** | Provide audit artifacts (Artifact) | Deterministic governance suite + control mappings as validation evidence; support CSV/CSA **(C)** | **Own validation acceptance**; approve validation plan and sign-off |
| **IdP / role mapping** | Cognito, IAM, STS primitives | Cognito pool with `custom:hpp_role`; gateway consumes role claim **(I/C)** | **Integrate enterprise IdP**; own role definitions and joiner/mover/leaver |
| **Connector integration** | Networking, Lambda, HealthLake, Secrets Manager | Connector framework (14 kinds, fixture/live); typed adapters **(I/C)** | **Provide live-system access, credentials, scopes**; validate live connectors |
| **Bedrock Guardrail config** | Guardrails service | Ship Guardrail with PHI filters + denied topics (unauthorized determination) + grounding **(I/C)** | Approve/tune denied topics and thresholds for their policy |
| **Prompt / model change control** | Bedrock model availability | Hash-pinned prompt registry (CI fails on drift); model-version change control **(I)** | Approve model selection; ratify change-control governance |
| **Clinical & coverage accountability** | — | Withhold `issue_determination` from all agents; HITL gates; fairness screen **(I)** | **Own every clinical and coverage decision**; medical-director sign-off; member impact |
| **42 CFR Part 2 (SUD)** | — | Consent check before disclosure; Part 2 flag **(C)** | Own consent capture and Part 2 program designation |
| **Section 1557 / accessibility** | — | Accessibility + health-literacy pre-flight **(I)** | Own language-access program and member communications policy |
| **Audit & breach response** | CloudTrail; service durability | Append-only WORM audit; evidence capture procedures (runbooks) **(I/C)** | **Own breach risk assessment & notification** (Privacy Officer); incident decisions |
| **Incident response & DR** | Service-level resilience | Runbooks; PITR/WORM design; fail-closed gates **(I/C)** | Own IR program ownership, severity declaration, regulatory comms |
| **PCI (patient-pay)** | PCI-compliant infra services | Card masking (Luhn); no card data in prompts/audit; tokenized connector **(C)** | Own PCI scope/attestation; merchant relationship |

## How to use this matrix in an engagement

This matrix is the contractual spine of a deployment. Walk it row by row in the first
governance session and assign a named owner on each side for every **C** (Configurable)
and every Healthcare-Org responsibility. Two patterns recur and are worth stating plainly:

1. **AWS secures the cloud; it does not run your compliance program.** Under the AWS Shared
   Responsibility Model, AWS is responsible for security *of* the cloud — the BAA-eligible
   services, KMS, the physical and service infrastructure. Everything *in* the cloud —
   entitlements, role mapping, Guardrail thresholds, what counts as a high-risk write — is
   configured by the SI and owned by the Healthcare Org.

2. **The human gate is where accountability lands.** No control in this matrix transfers
   clinical or coverage accountability to the platform or to AWS. The accelerator
   guarantees an agent cannot exceed the human and cannot issue a determination; the
   Healthcare Org guarantees a qualified human makes the decision. That division is
   deliberate and non-negotiable.

## Reading the matrix

- **AWS** is responsible for the security *of* the cloud and for offering BAA-eligible
  services; it does not configure your entitlements or own your clinical decisions.
- **The SI** delivers the governed platform and configures it, and supports validation —
  but does not sign the customer's BAA with AWS, define the customer's roles, or make
  coverage decisions.
- **The Healthcare Org** remains the covered entity/plan: it owns the data, the BAA, the
  validation acceptance, the IdP, the live-system access, and — non-delegably — every
  clinical and coverage decision. The agent assists; the human, and the organization,
  decide.
