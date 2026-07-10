# Incident Response & Key Management (HPP)

Companion to `runbooks/INCIDENT-RESPONSE.md` (ops procedure) — this is the security/key view.

## Keys & secrets
| Key / secret | Purpose | Dev | Production |
|---|---|---|---|
| **JWT signing (IdP)** | Identity assertions the gateway verifies | Cognito-managed JWKS | Cognito/IdP managed; rotate per IdP policy; gateway verifies via JWKS (`jwt_verify.py`) |
| **Approval signing key** | Mint/verify bound approval tokens | `APPROVAL_SIGNING_SECRET` env | AWS Secrets Manager + KMS; reviewer service only; rotate ≤90d |
| **Audit signing key** | Seal the hash-chained audit records — **separate secret from approvals** so an approval-key compromise cannot forge audit entries | `AUDIT_SIGNING_SECRET` env | AWS Secrets Manager + KMS; audit sink only; rotate ≤90d |
| **Scoped-token secret** | Per-call tool tokens | `GATEWAY_TOKEN_SECRET` env | AgentCore Identity / STS (no static secret) |
| **Data KMS CMK(s)** | Encrypt audit/HITL/WORM at rest | n/a | KMS CMK per environment/data class; key policy least-privilege; rotation enabled |
| **Connector credentials** | EHR/clearinghouse/payer access | fixtures (none) | Secrets Manager; never in prompts/audit |

Rotation: signing keys support **overlapping validity** (verify old+new during rollover) so a
rotation never breaks in-flight approvals or sessions. No secret is ever written to a prompt, a
log, or the audit trail (PHI masker + no-secret-in-prompt rule).

## Incident classes & first actions
| Class | First action | Containment | Evidence |
|---|---|---|---|
| **Suspected PHI exposure** | Engage privacy officer; begin HIPAA breach 4-factor assessment | Revoke tokens; disable affected connector; rotate impacted keys | Append-only audit (PHI-masked), CloudTrail |
| **Signing-key compromise** | Rotate the key immediately (overlapping); invalidate sessions/approvals | Force re-auth; revoke standing grants | Secrets Manager versioning, audit |
| **Prompt-injection attempt** | Confirm the gateway **denied** the action (it should) | Tune Guardrail; add red-team case | redteam suite, audit |
| **Authorization anomaly** | Diff effective grants vs intent; freeze the agent | Tighten `policy.py`; redeploy | gateway tests, audit |
| **Audit-integrity alarm** | Run `verify_chain()`; compare WORM snapshot | Isolate; forensic copy from Object Lock | `audit.py`, S3 Object Lock |
| **Guardrail trip spike / cost** | Throttle at WAF; check quotas | Scale down; investigate source | CloudWatch, WAF |

## Evidence handling
The audit trail is **append-only and hash-chained**; never edit it. Pull forensic copies from the
S3 Object Lock (WORM) bucket — retention prevents deletion until it elapses (by design). Bind
every action in the incident timeline to its audit record (actor, tool, approver, lineage).
