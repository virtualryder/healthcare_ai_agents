# Security Policy

## Status & scope
This repository is a **governed reference accelerator** for Health Providers & Plans (HPP)
agentic AI on AWS. It is **not** an AWS-authorized, HITRUST-certified, or otherwise authorized
production system. The Python control plane is a **reference implementation** of the
authorization, approval, token, audit, and PHI-masking semantics; production deployments
substitute the managed AWS equivalents (Amazon Bedrock AgentCore Gateway/Identity, API Gateway +
Cognito + Verified Permissions/Cedar, STS, KMS, DynamoDB, S3 Object Lock). PHI requires an
executed **AWS Business Associate Agreement (BAA)** before go-live. See
`docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`.

## Reporting a vulnerability
Report suspected vulnerabilities privately to the maintainer: **ryderdavid75@gmail.com**
(subject: `SECURITY — healthcare_ai_agents`). Include affected file/commit, reproduction, and
impact. Do **not** open a public issue for an unfixed vulnerability. Target: acknowledgement in
5 business days; triage + remediation plan in 15.

## In scope
- The Python control plane (`platform_core/`, `governance/`, `care_platform/`, `aws-native-reference/`).
- Infrastructure-as-code (`infra/cloudformation/`, `infra/terraform/`).
- The deny-by-default authorization model, bound human-approval gate, scoped tokens, append-only
  hash-chained audit, and PHI masking.

## Out of scope (customer / deployer responsibility)
- The customer's IdP federation and entitlement source of truth.
- Live connectors to systems of record (EHR/FHIR, clearinghouse, payer portals, Amazon Connect).
- HITRUST / SOC 2 authorization, third-party penetration testing, continuous monitoring.
- Production secret material (KMS keys, token-signing keys), retention schedules, and DR.

## Security model (summary) — defense in depth, fail-closed
1. **Cryptographic identity** — RS256/JWKS JWT verification with an algorithm allow-list and an
   alg-confusion guard (`platform_core/hpp_agent_platform/jwt_verify.py`); client-supplied roles
   are never trusted.
2. **Deny-by-default authorization** — least privilege as the intersection of agent grant ∩ user
   entitlement (`mcp_gateway/policy.py`); consequential authorities (submit a claim, issue a UM
   determination) are withheld from every agent and proven by tests.
3. **Bound human approval** — single-use, separation-of-duties, tamper-evident approval tokens
   cryptographically bound to the exact tool + arguments (`approvals.py`).
4. **Scoped, short-lived tokens** — per-call, tool-scoped, expiring (`mcp_gateway/tokens.py`).
5. **Append-only, hash-chained audit + WORM** — chained records + (prod) conditional writes with
   an IAM Update/Delete deny + S3 Object Lock (`mcp_gateway/audit.py`, `audit_sinks.py`,
   `infra/cloudformation/data.yaml`).
6. **Fail-closed PHI masking** (`phi.py`, HIPAA Safe Harbor identifiers) + **Bedrock Guardrails**
   on input and output.
7. **In-account inference** — Bedrock via VPC endpoint under the AWS BAA; no PHI egress.

Full threat model: `docs/THREAT-MODEL.md`. Control-to-NIST mapping:
`docs/NIST-800-53-CONTROL-MATRIX.md`. OWASP-LLM / MITRE ATLAS mapping:
`docs/OWASP-LLM-ATLAS-MAPPING.md`. IR & key management: `docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md`.

## Supported versions
Pre-1.0 reference accelerator: only the latest `main` is supported. See `CHANGELOG.md` / `VERSION`.
