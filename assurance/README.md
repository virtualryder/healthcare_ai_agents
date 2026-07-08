# Healthcare Payer/Provider (HPP) Agentic AI Suite — Auditor & GRC Assurance Packet

**Cover sheet and curated index for a healthcare security reviewer, HIPAA assessor, or GRC /
TPRM team.** This packet does not duplicate content — it points to the artifacts already in
this repository, organized under standard assurance headings. Links are relative to the
repository root.

---

## 1. Purpose & scope

Eight healthcare payer/provider agents on the shared Aegis control plane, built on AWS. This
packet lets a reviewer answer a HIPAA / 42 CFR Part 2 / vendor-risk questionnaire directly from
repository artifacts.

> **Honesty line.** This suite is a **reference accelerator, not an ATO'd product and not a
> compliance certification.** It ships control *design* and reference IaC. The AWS BAA, control
> operation on live PHI, evidence generation, and accountability for compliance are
> **customer-owned**. See the maturity matrix in [`../README.md`](../README.md) for Implemented
> vs. Configurable (customer-owned).

---

## 2. Architecture & data-flow diagrams

- PHI data flow (masking before model and audit; Bedrock under the AWS BAA) — [`../docs/diagrams/phi-data-flow.svg`](../docs/diagrams/phi-data-flow.svg) ([PNG](../docs/diagrams/phi-data-flow.png))
- MCP gateway authorization flow (shared control plane, deny paths) — [`../docs/diagrams/mcp-gateway-auth-flow.svg`](../docs/diagrams/mcp-gateway-auth-flow.svg) ([PNG](../docs/diagrams/mcp-gateway-auth-flow.png))
- Suite architecture (edge-to-data narrative) — [`../docs/SUITE-ARCHITECTURE.md`](../docs/SUITE-ARCHITECTURE.md)
- AWS Well-Architected review — [`../docs/WELL-ARCHITECTED-REVIEW.md`](../docs/WELL-ARCHITECTED-REVIEW.md)

## 3. Threat model & abuse cases

- STRIDE threat model, abuse cases, threat → control → file — [`../docs/THREAT-MODEL.md`](../docs/THREAT-MODEL.md)

## 4. Control mappings (NIST 800-53, NIST AI RMF; HIPAA / 42 CFR Part 2)

- NIST 800-53 control matrix — [`../docs/NIST-800-53-CONTROL-MATRIX.md`](../docs/NIST-800-53-CONTROL-MATRIX.md)
- Regime mappings: HIPAA Privacy/Security, 42 CFR Part 2, HITECH, NIST AI RMF — [`../docs/COMPLIANCE-CONTROL-MAPPINGS.md`](../docs/COMPLIANCE-CONTROL-MAPPINGS.md)
- OWASP LLM Top-10 + MITRE ATLAS mapping — [`../docs/OWASP-LLM-ATLAS-MAPPING.md`](../docs/OWASP-LLM-ATLAS-MAPPING.md)
- Governance controls (code) — [`../governance/controls/`](../governance/controls/)

## 5. Identity, authorization & human-in-the-loop controls

- Deny-by-default MCP gateway, JWT + `custom:hpp_role` re-verification, scoped per-call tokens, minimum-necessary at the gateway — [`../docs/WHY-THE-MCP-LAYER.md`](../docs/WHY-THE-MCP-LAYER.md), [`../docs/SUITE-ARCHITECTURE.md`](../docs/SUITE-ARCHITECTURE.md)
- IdP federation runbook — [`../docs/IDP-FEDERATION-RUNBOOK.md`](../docs/IDP-FEDERATION-RUNBOOK.md)
- Consequential-commit / human-gate controls & red-team — [`../governance/redteam/`](../governance/redteam/), [`../governance/tests/`](../governance/tests/)

## 6. Data protection (encryption, masking, WORM audit, residency)

- Encryption / key management (KMS CMK), hash-chained append-only audit, WORM — [`../docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md`](../docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md)
- PHI masking (Safe Harbor) at every boundary — see [`../docs/SUITE-ARCHITECTURE.md`](../docs/SUITE-ARCHITECTURE.md) and threat model T-series
- Residency: PHI stays in the customer's AWS account/region under the AWS BAA; residency guarantees are **customer-owned** (region pinning, PrivateLink endpoint policy).

## 7. Deployment evidence

- Clean-account acceptance run — [`../evidence/CLEAN-ACCOUNT-ACCEPTANCE.md`](../evidence/CLEAN-ACCOUNT-ACCEPTANCE.md)
- No standalone `DEPLOYED-AND-VALIDATED.md` in this repo — deployment validation is summarized in [`../README.md`](../README.md) ("Validation update") and [`../docs/DEPLOY-QUICKSTART.md`](../docs/DEPLOY-QUICKSTART.md).

## 8. Security testing (pen-test, CI gates, SBOM)

- Pen-test scope: **not present as a standalone doc** — customer-owned; nearest equivalent is the threat model + incident-response docs above.
- CI security gates — [`../.github/`](../.github/) workflows; full test suite via `make test`.
- SBOM: not present as a static artifact — **customer-owned**, generated per build/release.
- Third-party risk (TPRM) due-diligence packet — [`../offerings/TPRM-DUE-DILIGENCE-PACKET.md`](../offerings/TPRM-DUE-DILIGENCE-PACKET.md)

## 9. Shared-responsibility / RACI

- Production-readiness & shared-responsibility split — [`../docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`](../docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md)
- Shared-responsibility matrix — [`../docs/SHARED-RESPONSIBILITY-MATRIX.md`](../docs/SHARED-RESPONSIBILITY-MATRIX.md)
- Incident response runbook — [`../runbooks/INCIDENT-RESPONSE.md`](../runbooks/INCIDENT-RESPONSE.md)

## 10. Known limitations & maturity

- Capability maturity matrix — [`../README.md`](../README.md) (§ "Capability maturity matrix")
- Suite status — [`../SUITE-STATUS.md`](../SUITE-STATUS.md)

## 11. Contact & reporting

- Vulnerability reporting via **GitHub Security Advisories** (repository *Security* tab →
  *Report a vulnerability*) — see [`../SECURITY.md`](../SECURITY.md). Do not open public issues
  for security reports.

---

*Reference accelerator — not an AWS service, not AWS-supported software, not a compliance
certification, and not production-ready for regulated data without customer-specific
engineering, testing, authorization, and operational ownership.*
