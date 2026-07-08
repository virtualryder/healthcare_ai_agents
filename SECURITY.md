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
Report vulnerabilities privately via GitHub Security Advisories: use the *Security* tab →
*Report a vulnerability* on this repository. Please do not open public issues for security
reports. Include affected file/commit, reproduction, and impact. Target: acknowledgement in
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
6. **Fail-closed PHI masking** (`phi.py`, HIPAA Safe Harbor identifiers; deterministic by default,
   with optional HIPAA-eligible Amazon Comprehend Medical `DetectPHI` under `PHI_ENGINE=comprehend_medical`
   — see *PHI masking engines* below) + **Bedrock Guardrails** on input and output.
7. **Private-connectivity inference** — Bedrock via VPC endpoint (AWS PrivateLink) under the AWS BAA; no PHI egress to external AI APIs — traffic to the regional Bedrock service stays on AWS private networking.

### PHI masking engines (deterministic default vs. Comprehend Medical opt-in)
The fail-closed PHI masker (`platform_core/hpp_agent_platform/phi.py`) supports two engines
at the log/audit boundary. Whichever engine runs, the **deterministic Safe-Harbor pass always
executes** — it is the always-on baseline, never bypassed.

- **Deterministic (default).** Dependency-free regex + Luhn masker covering the HIPAA Safe
  Harbor identifier families (SSN, MRN, member/beneficiary IDs, account/claim numbers, dates
  more specific than year, email, phone, address, payment cards, device IDs). No network call,
  no external dependency. This is the engine unless a flag is set.
- **Amazon Comprehend Medical (opt-in).** Set `PHI_ENGINE=comprehend_medical` to *additionally*
  run Comprehend Medical `DetectPHI` (`platform_core/hpp_agent_platform/comprehend_medical.py`)
  before re-running the deterministic pass — **belt and suspenders: Comprehend Medical + regex,
  never one alone.** An optional `PHI_COMPREHEND_MIN_CONFIDENCE` threshold gates which detected
  spans redact. `boto3` is imported lazily, so the dependency is optional; the golden-path IAM
  role grants `comprehendmedical:DetectPHI` only when this flag is selected
  (`infra/golden-path-01-revenue-cycle/template.yaml`, `PhiEngine=comprehend_medical`).
- **Fail-closed contract (both engines).** Any error in the ML engine — missing `boto3`, client
  build failure, throttling, `ClientError`, malformed response, bad offsets — falls back to the
  deterministic Safe-Harbor output with an audit-visible `ML_MASK_FALLBACK_FLAG`; if even the
  deterministic pass raised, the payload is replaced with `MASK_FAILURE_PLACEHOLDER`. Unmasked
  input is **never** returned from any path.
- **HIPAA eligibility & residency.** Amazon Comprehend Medical is a **HIPAA-eligible** service,
  usable for PHI under an executed **AWS BAA**. In the golden-path deployment it is reached over
  the **regional Comprehend Medical API via an interface VPC endpoint (AWS PrivateLink)** — traffic
  to the regional service stays on AWS private networking under the BAA; PHI is processed by the
  AWS managed service, not sent to any non-AWS third-party AI API.

Full threat model: `docs/THREAT-MODEL.md`. Control-to-NIST mapping:
`docs/NIST-800-53-CONTROL-MATRIX.md`. OWASP-LLM / MITRE ATLAS mapping:
`docs/OWASP-LLM-ATLAS-MAPPING.md`. IR & key management: `docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md`.

## Supported versions
Pre-1.0 reference accelerator: only the latest `main` is supported. See `CHANGELOG.md` / `VERSION`.
