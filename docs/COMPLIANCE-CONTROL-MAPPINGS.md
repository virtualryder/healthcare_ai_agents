# Compliance Control Mappings — Narrative Companion

This is the prose companion to `governance/controls/control_mappings.py`. That module is the
machine-readable source of truth — each entry ties a regulatory regime to the concrete
platform control that addresses it, the AWS service that backs it, and a maturity status.
This document narrates those mappings for a CISO, privacy officer, or HITRUST/SOC 2 assessor:
*why* each control is defensible, and *what remains the customer's to configure*.

**Maturity legend** (matching the module's `status` field):
- **Implemented** — built into the accelerator and exercised by the test/governance suite.
- **Configurable** — the mechanism ships; it must be configured/connected per customer.
- **Customer** — owned by the Healthcare Org (none of the rows below are purely Customer; all
  pair a platform control with a customer configuration responsibility called out in text).

## The mapping, regime by regime

### HIPAA Privacy Rule (45 CFR 164.5xx) — minimum necessary — *Implemented*
**Control:** deny-by-default gateway + least-privilege intersection (agent grant ∩ user
entitlement) + scoped tokens per tool. **AWS:** Bedrock AgentCore Gateway/Identity (or API
Gateway + Cognito + STS). The agent can request only the lesser of its grant and the user's
entitlement, which is "minimum necessary" enforced in code. *Customer configures the
entitlement model and role definitions.*

### HIPAA Security Rule (45 CFR 164.312) — access/audit/integrity — *Configurable*
**Control:** append-only PHI-masked audit; tamper-evident trail; encryption; per-call
attribution. **AWS:** DynamoDB (deny Update/Delete) + S3 Object Lock WORM + KMS + CloudTrail.
Addresses access control, audit controls, and integrity simultaneously. *Customer ratifies
retention, key policy, and CloudTrail scope.*

### HIPAA / AWS BAA — PHI only under a BAA — *Configurable*
**Control:** in-account Bedrock inference (no external API egress); BAA-eligible services
only. **AWS:** Amazon Bedrock (HIPAA-eligible) + VPC endpoints + Guardrails. Keeps PHI inside
the account and under the AWS BAA. *Customer must execute the AWS BAA (and a BAA with the SI).*

### HITECH Act — breach notification / enforcement — *Implemented*
**Control:** PHI masking at every log/audit boundary; no raw identifiers in traces. **AWS:**
governance + PHI masker + CloudWatch. Reduces breach surface by ensuring identifiers never
reach logs. *Customer owns the breach risk assessment and notification decision.*

### 42 CFR Part 2 — SUD record protection — *Configurable*
**Control:** sensitive-data consent check before disclosure; Part 2 flag on the consent
connector. **AWS:** gateway `consent.check` + segmented data class + KMS. Enforced for agents
03 and 07. *Customer owns consent capture and Part 2 program designation.*

### CMS-0057-F Interoperability & Prior Auth — FHIR APIs / PA reasons — *Configurable*
**Control:** Da Vinci-aligned payer connector (CRD/DTR/PAS); structured PA assembly + status.
**AWS:** HealthLake (FHIR) + API Gateway + Lambda. Supports the four FHIR APIs due Jan 1,
2027 and PA denial-reason/turnaround provisions. *Customer connects live payer/FHIR
endpoints.*

### No Surprises Act — Good Faith Estimate — *Implemented*
**Control:** deterministic cost-estimate tool (`registration.estimate_cost`) with GFE basis +
disclaimer. **AWS:** gateway + deterministic rules + Step Functions. Agent 04's estimate is
deterministic (no model), so it is exact and reproducible. *Customer supplies the pricing
source.*

### Section 1557 / ADA (45 CFR Part 92) — accessible, nondiscriminatory comms — *Implemented*
**Control:** accessibility + health-literacy pre-flight on patient-facing output. **AWS:**
governance/accessibility + CI (axe-core). Runs before member-facing text is returned.
*Customer owns its language-access program.*

### 21st Century Cures Act (info-blocking) — no improper EHI interference — *Configurable*
**Control:** read tools surface, never withhold, lawful EHI; security-trimmed retrieval with
audit. **AWS:** HealthLake + Knowledge Bases ACL propagation + CloudTrail. The agent doesn't
become a new info-blocking vector. *Customer configures ACLs and retrieval scopes.*

### CMS rules on AI in UM / MA prior auth — human decides, no algorithmic denial — *Implemented*
**Control:** `issue_determination` withheld from all agents; HITL gate; fairness screen on
flag/rank. **AWS:** gateway policy + governance/fairness + Step Functions `waitForTaskToken`.
The architectural guarantee behind agent 05: an adverse recommendation is forwarded to the
medical director, never auto-denied. *Customer staffs the medical-director gate.*

### NIST AI RMF 1.0 / model governance — Govern/Map/Measure/Manage — *Implemented*
**Control:** grounding verification; prompt registry; evals; red team; fairness; HITL gates.
**AWS:** governance/* + CloudWatch. The full model-risk discipline runs in CI. *Customer
ratifies the governance and change-control process.*

### HITRUST CSF / SOC 2 — assessable control set — *Configurable*
**Control:** control mappings as evidence; deterministic governance suite runnable in CI.
**AWS:** governance + AWS Artifact + Security Hub. This very mapping is the evidence spine.
*Customer engages the assessor and owns certification.*

### PCI DSS (patient-pay) — protect cardholder data — *Configurable*
**Control:** card masking (Luhn); no card data in prompts/audit; tokenized payment connector.
**AWS:** gateway + PHI masker + payment provider. Keeps the agent and audit out of PCI scope.
*Customer owns PCI attestation and the merchant relationship.*

## How an assessor should read this

Pair this narrative with the live `control_mappings.py` (and `by_regime()` for filtering).
**Implemented** rows are demonstrable today against the test/governance suite;
**Configurable** rows are where the engagement does its work — connecting systems, executing
the BAA, integrating the IdP, and tuning thresholds. The maturity column is deliberately
honest: it tells you exactly which controls are evidence-ready and which require customer
configuration before a production attestation.
