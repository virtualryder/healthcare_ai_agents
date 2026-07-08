# NIST SP 800-53 Rev 5 — Control Matrix (HPP)

Control-by-control: how the accelerator addresses each, the evidence (code/test/IaC), and who
owns the residual. Status: **Implemented** (in this repo) · **Configurable** (customer wires it)
· **Customer** (customer-owned). This complements `governance/controls/control_mappings.py`
(machine-readable regime→control→AWS) and supports a HITRUST/SOC 2 evidence package.

| NIST control | How addressed | Evidence | Status |
|---|---|---|---|
| **AC-2 Account Mgmt** | Cognito user pool + `custom:hpp_role`; least-privilege agent role | `security.yaml`, `terraform/modules/security` | Configurable |
| **AC-3 Access Enforcement** | Deny-by-default gateway; agent grant ∩ user entitlement | `mcp_gateway/policy.py`; gateway tests | Implemented |
| **AC-4 Information Flow** | All system access via the governed connector; no direct vendor SDK calls | `connectors/`, gateway | Implemented |
| **AC-5 Separation of Duties** | Bound approval: reviewer ≠ requester (mint + verify) | `approvals.py`; test_security_controls | Implemented |
| **AC-6 Least Privilege** | Consequential tools withheld from agents; per-call scoped tokens | `policy.py`, `tokens.py` | Implemented |
| **AU-2/AU-3 Audit Events/Content** | Every ALLOW/DENY/PENDING/ERROR recorded with lineage + actor | `mcp_gateway/audit.py` | Implemented |
| **AU-9 Protection of Audit Info** | Hash-chained append-only; prod conditional writes + IAM deny + S3 Object Lock | `audit.py`, `audit_sinks.py`, `data.yaml` | Implemented / Configurable |
| **AU-10 Non-repudiation** | Tamper-evident chain (`verify_chain`); approver bound into the record | `audit.py` | Implemented |
| **IA-2/IA-5 Identification & Auth** | RS256/JWKS verification; alg-confusion guard; no trusted client roles | `jwt_verify.py`; test_security_controls | Implemented |
| **IA-8 Non-org users (members)** | Member identity verified before disclosure (agents 04/08) | `identity.verify_member` | Implemented |
| **SC-7 Boundary Protection** | CloudFront+WAF+Shield edge; private subnets; VPC endpoints | `infra/`, THREAT-MODEL | Configurable |
| **SC-8 Transmission Confidentiality** | TLS in transit; Bedrock via VPC endpoint/PrivateLink (no PHI egress to external AI APIs) | `network.yaml`, `llm_factory.py` | Configurable |
| **SC-12/SC-13 Key Mgmt / Crypto** | KMS CMK per environment; signing keys via Secrets Manager | `security.yaml`, `secrets.py`, IR-KM doc | Configurable |
| **SC-28 Protection at Rest** | KMS-encrypted DynamoDB + S3; Object Lock WORM | `data.yaml` | Configurable |
| **SI-4 System Monitoring** | CloudTrail/GuardDuty/Security Hub/Config (customer); structured PHI-masked traces | `tracing.py`, runbooks | Configurable |
| **SI-10 Input Validation** | Bedrock Guardrails (PHI filters, prompt-attack); grounding verification | `llm_factory.py`, `governance/grounding.py` | Implemented |
| **RA-5 Vulnerability Mgmt** | CI runs tests + lint; pen test is customer engagement | `.github/workflows/ci.yml` | Implemented / Customer |
| **CM-3 Change Control (model risk)** | Hash-pinned prompt registry; CI fails on drift | `governance/prompt_registry.py` | Implemented |
| **IR-4 Incident Handling** | IR runbook + key-compromise playbook | `INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md`, `runbooks/INCIDENT-RESPONSE.md` | Implemented |
| **CP-9/CP-10 Backup/Recovery** | PITR on audit/HITL; WORM retention; DR runbook (RPO/RTO) | `data.yaml`, `runbooks/DR-RUNBOOK.md` | Configurable |
| **PT-* / Privacy (HIPAA)** | PHI masking (Safe Harbor); minimum-necessary at the gateway; consent (42 CFR Part 2) | `phi.py`, `policy.py`, consent | Implemented |

> The **PE/MA/PS** (physical, maintenance, personnel) families are inherited from AWS (under the
> BAA) and the customer's program — out of scope for the accelerator code.
