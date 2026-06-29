# HPP / HCOS — External Review: Validation & Remediation Plan

**Review source:** independent static assessment (ChatGPT), scored **60/100 as a deployable product / 84/100 as a sales-and-architecture accelerator.**
**This document:** our independent validation of every material finding against the actual code, plus a prioritized plan to close the gap between what the README claims and what the deployed AWS path enforces.

**Bottom line up front:** the review is **substantially correct.** We confirmed each material finding against repo files. The repository is an excellent *accelerator* and a genuine *reference control plane*, but several controls described as "implemented and tested" live only in the local Python layer and are **not wired into the deployed AWS path** (golden path / CloudFormation). The fastest credible path forward is the review's own recommendation: **stop widening the 8-agent suite and make Agent 01 one complete, proven, end-to-end-tested product** on a single canonical architecture, then let Agents 02–08 inherit a control plane that has actually been proven rather than only modeled.

---

## 1. Validation of findings (evidence-based)

Legend: ✅ Confirmed · ◐ Confirmed with nuance · ❌ Not reproduced

| # | Finding | Verdict | Evidence in repo | Severity |
|---|---------|---------|------------------|----------|
| F1 | AWS templates implement a stronger architecture in the README than in the IaC; several paths are scaffolding | ✅ | `infra/cloudformation/agent-service.yaml:28,36` Step Functions states are `"Type":"Pass"` placeholders; connector Lambda is an echo handler | High |
| F2 | Golden-path approval bypass — caller-supplied approval reaches the gateway; demo path accepts an *unauthenticated* reviewer (only checks reviewer≠requester) | ✅ | `golden-path-01-revenue-cycle/src/index.py:45` passes `approval=body.get("approval")`; `mcp_gateway/gateway.py` `_approval_ok` returns `True` for `{approved:true, reviewer:{sub≠requester}}` with no reviewer authentication | **P0 / blocker** |
| F3 | Smoke test does not exercise two-person approval, argument tampering, or replay | ✅ | `golden-path-01-revenue-cycle/smoke_test.sh` covers ALLOW-read / PENDING-write / DENY-withheld only | High |
| F4 | Deployed audit ≠ README audit — DynamoDB append-only sink exists but is **not wired** into the golden-path Lambda (defaults to in-memory); chain state is in-process, resets on cold start, branches under concurrency; S3 Object Lock export not in the transaction path | ✅ | `audit_sinks.py` has `DynamoDBAppendOnlySink` but `golden-path/src/index.py` instantiates none → default `GatewayAuditLog()` (in-memory, `audit.py:51` `self.records=[]`, `:53` `_last_hash` in process) | **P0 / blocker** |
| F5 | Network does not enforce the data-residency claim — Bedrock VPC endpoint exists, but Lambdas are **not** VPC-attached and private subnets egress via NAT to `0.0.0.0/0` | ✅ | `network.yaml:49` NatGateway, `:66` private route `0.0.0.0/0`→NAT; no `VpcConfig` on any Lambda (`connectors.yaml`, golden-path `template.yaml`) | **P0 / blocker** |
| F6 | Enterprise identity not deployed — Cognito user pool + client only, no SAML/OIDC federation, no group→role mapping | ✅ | `security.yaml` has no `AWS::Cognito::UserPoolIdentityProvider` | High |
| F7 | IAM not separated — one role trusted by Lambda+States+ECS+AgentCore; Bedrock `Resource:"*"` | ✅ | `security.yaml:74` four-service trust principal; `:81` `bedrock:InvokeModel/ApplyGuardrail Resource:"*"`; `:21` another `Resource:"*"` | High |
| F8 | AgentCore target incomplete — MCP Lambda target missing required `ToolSchema` | ✅ | `agentcore-gateway.yaml:26,33` `Mcp:{Lambda:{LambdaArn:…}}` with no `ToolSchema` (cfn-lint passed because it lacks the resource's full schema) | Medium |
| F9 | PHI masking optional ML path is fail-**open** | ◐ | `phi.py:125` `except Exception: return text`. Nuance: this affects only the **opt-in** `MASK_ENGINE=ml` hook; the default deterministic regex path always returns masked text (not fail-open). Still must fail-closed | Medium |
| F10 | CI validates reference code, not deployment viability (no ephemeral deploy, no SAST/secret/IaC/dep/container scanning, no SBOM/signing/provenance) | ✅ | `.github/workflows/ci.yml` = lint + unit tests only; no `terraform validate`/`plan`, no trivy/bandit/semgrep/gitleaks/cosign/sbom | High |
| F11 | Maturity-message inconsistency between SUITE-STATUS ("all 8 built to reference depth") and the more conservative field-guide framing | ◐ | `SUITE-STATUS.md:28` "ALL 8 AGENTS BUILT"; `gtm/SELLER-SA-FIELD-GUIDE.md:5` "Demonstrated and Deployable-by-design." Reality: all 8 reach **Demonstrated** code depth, but only **Agent 01** has the golden-path + live-connector proof. Need one precise, capability-scoped taxonomy | Medium |

**Net:** 9 confirmed, 2 confirmed-with-nuance, 0 refuted. The headline production blockers are **F2 (approval bypass), F4 (audit not durable/wired), and F5 (egress/residency not enforced)** — exactly the three a CISO will fail us on.

---

## 2. The one decision that unblocks everything: pick a canonical architecture

The repo currently exposes ~8 partially-equivalent paths (local LangGraph, framework-free runner, SAM golden path, nested CloudFormation, Terraform, AWS-native Step Functions, ECS/Fargate, AgentCore Gateway). A director of architecture will ask which one is *supported, tested, versioned, monitored, operated.* Today there is no single answer.

**Decision: Agent 01 (Revenue-Cycle & Denial) on the SAM golden path is THE canonical, supported, production-track reference.** Every other path is explicitly relabeled **"alternative reference (not the supported deployment)"** until it passes the same acceptance test. AgentCore becomes a documented *roadmap target*, not a claimed equivalent.

Everything in §3 hardens that one path.

---

## 3. Prioritized remediation plan

### P0 — required before we describe any AWS path as "deployable" (close F2, F4, F5 + the IAM/scoping pieces a pilot needs)

1. **Deploy a real reviewer service (kills the approval bypass, F2).**
   A separate Lambda behind its *own* Cognito authorizer: it authenticates the reviewer independently, re-reads the exact pending request from the audit/HITL table, enforces reviewer≠requester, and **mints the cryptographically-bound, single-use approval token** (`approvals.mint_approval`) bound to {agent, tool, canonical-args-hash, requester}. The connector Lambda then only ever accepts `approval={"token": …}`.
   - **Remove the demo approval path from deployed environments.** Add `AUTH_REQUIRE_BOUND_APPROVAL=1` (gateway env): when set, `_approval_ok` rejects the `{approved, reviewer}` shape outright — a bare `approved:true` can never authorize a production action. Demo path stays available only for local fixtures.
   - *Accept:* a requester-fabricated reviewer is denied; only a token minted by the reviewer service authorizes the write.

2. **Durable replay protection (F2/F4).** Replace the in-process `self._seen_jti` set with a **DynamoDB conditional write** (`attribute_not_exists(jti)`) so an approval token is consumed exactly once across concurrent Lambda environments. *Accept:* replaying a used token → DENY; modified args → DENY (binding hash mismatch).

3. **Wire the durable audit sink into the gateway on the golden path (F4).** Golden-path Lambda constructs `MCPGateway(audit=GatewayAuditLog(sink=DynamoDBAppendOnlySink(table=$AUDIT_TABLE)))`. Fix the chain design for concurrency/durability: per-record conditional put keyed by a monotonic sequence (or adopt QLDB-style/verifiable-ledger semantics), writer IAM with **no** Update/Delete, and a tested **S3 Object Lock (COMPLIANCE/WORM) export** in the finalize step. *Accept:* audit survives cold starts, rejects out-of-order/duplicate sequence, and `verify_chain` passes on the DynamoDB-backed trail.

4. **Enforce the network model (F5).** Attach every runtime Lambda to the private subnets (`VpcConfig`); add the interface endpoints it actually needs (Bedrock runtime, STS, DynamoDB gateway endpoint, KMS, Logs, S3); add restrictive **endpoint policies**; remove the NAT/`0.0.0.0/0` egress for runtime subnets (or replace with an explicit deny-by-default egress SG). *Accept:* an integration test from inside the function proves Bedrock resolves over PrivateLink and a direct public-internet call fails.

5. **Separate IAM roles + scope Bedrock (F7).** Distinct least-privilege roles: state-machine execution, each Lambda, reviewer service, audit writer, WORM exporter, connector, CI/CD. Scope `bedrock:InvokeModel`/`ApplyGuardrail` to the specific **model ARN + guardrail ARN**, not `"*"`. Connector role scoped to its approved tool operations and exact resources.

6. **One real sandbox connector (F1).** Replace the echo Lambda for Agent 01 with one customer-relevant **sandbox** integration (e.g., a payer/clearinghouse FHIR or X12 277/835 sandbox) wired through the existing live-connector façade, with authentication, idempotency keys, retries, timeouts, circuit-breaking, reconciliation, and lineage capture.

7. **Implement the real state machine (F1).** Replace the `Pass` placeholders in `agent-service.yaml` with the actual Lambda tasks: load → analyze → gather-evidence → draft → compliance-check → `waitForTaskToken` human gate (fed by the reviewer service) → finalize (export to a **controlled queue**, not auto-submit) → durable audit.

8. **Clean-account acceptance test as a release gate (F3/F10).** Automate the full sequence below; nothing is called "deployable" until it passes in a fresh account and tears down cleanly.

### P1 — required before a PHI pilot

9. **Enterprise federation + role mapping (F6):** add `UserPoolIdentityProvider` (SAML/OIDC), hosted domain, and group→`custom:hpp_role` mapping — or, if left to the customer, document it as a **required** post-deploy step in the runbook with exact resources.
10. **Fail-closed PHI logging (F9):** if masking raises (including the ML hook), **do not** log the record — drop to a non-PHI security metric + remediation queue; never return unmasked input. Make `_ml_mask` re-raise; wrap the audit write so a mask failure blocks the write.
11. **Supply-chain CI (F10):** add `terraform validate`/`plan`, gitleaks (secrets), bandit/semgrep (SAST), pip-audit (deps), checkov/trivy-config (IaC), trivy (container), SBOM (syft) + image signing (cosign) + release provenance + immutable tagged releases.
12. **README capability-status matrix + maturity taxonomy (F11)** — see §5.

### P2 — production hardening / the remaining agents

13. Fix the **AgentCore** target `ToolSchema` + authorization policy + identity config + integration test before describing AgentCore as equivalent (F8).
14. Bring **container/Fargate** and **Terraform** paths to the same acceptance bar, or label them "alternative reference."
15. Only after Agent 01 passes end-to-end, **propagate** the proven control plane to Agents 02–08.

---

## 4. The acceptance test (release gate) — adopt verbatim

A release is not "deployable" until automation proves, in a clean AWS account:

Deploy clean account → federate requester + reviewer identities → start a denial workflow → retrieve synthetic/sandbox evidence → generate a grounded draft → **block self-approval** → **block fabricated-reviewer identity** → **block unauthorized role** → approve via the authenticated reviewer service → **execute the exact approved action once** → **reject modified arguments** → **reject replay** → verify the durable audit record → verify WORM export → **verify prohibited egress is blocked** → verify alarms/logs/traces → destroy cleanly.

The bolded steps are precisely what today's smoke test does not cover.

---

## 5. README changes (truth-in-labeling)

Add a capability-status matrix and apply one consistent label set so a CISO sees exactly where each control stands.

| Capability | Local demo | Golden path (today) | Production (required) |
|---|---|---|---|
| Fixture connector | Implemented | Implemented | Replace with live |
| Live EHR/clearinghouse connector | Reference interface | Not complete | Required |
| Human approval | Simulated/reference | **Incomplete (bypassable)** | Authenticated reviewer service |
| Durable replay protection | Unit-tested concept | **Not wired** | Required (DynamoDB conditional) |
| Immutable audit | In-memory reference | **Not wired** | DynamoDB append-only + WORM |
| Enterprise IdP | N/A | Cognito base only | Federation required |
| Private Bedrock access | Design pattern | Endpoint only, runtime path unproven | Enforce + test |
| WORM retention | Design pattern | Resource/reference | Operational export |
| Container / AgentCore mode | Described | Incomplete | Build + validate |

**Maturity labels** (replace mixed wording everywhere): *Implemented & integration-tested · Implemented, needs configuration · Reference implementation · Infrastructure skeleton · Customer responsibility · Not yet implemented.* And soften the residency claim to: *"the target architecture supports private, in-account Bedrock inference when the runtime is VPC-attached and private connectivity is configured and verified."*

---

## 6. Defensible positioning (until P0 lands)

Position as: **"a governed healthcare AI workflow accelerator on AWS, led by revenue-cycle denial management"** — reusable governance control plane + reference infrastructure + synthetic fixtures + security mappings + customer collateral; live integration, customer identity, validation, and production assurance completed during implementation. Do **not** position as "8 production-ready agents deployable unchanged."

---

## 7. Sequencing & ownership

- **Code/IaC we can do in-repo now:** F2 (bound-approval enforcement flag + reviewer-service template), F4 (wire DynamoDB sink + WORM export step + concurrency-safe sequencing), F5 (VpcConfig + endpoints + egress lockdown), F7 (role split + Bedrock ARN scoping), F1/F6–F11 templates, the acceptance-test harness, CI scanning, and the README matrix. These are the bulk of P0/P1.
- **Customer-engagement (not code):** AWS BAA, real IdP wiring, validating live connectors against the customer's Epic/Oracle Health / Change Healthcare / payer endpoints, Bedrock Guardrail tuning, penetration test, HITRUST/SOC 2 evidence.

> **Progress (2026-06-29):** P0 #1–#3 + #5 (reviewer service, bound-approval enforcement, durable replay, durable DynamoDB audit, separated function roles + scoped Bedrock) and #4 (network model: private subnets, no IGW/NAT, VPC endpoints for DynamoDB/KMS/Logs/STS/Bedrock, egress-locked SGs, `/egress-check` probe) are DONE — 153 tests green, cfn-lint clean. #7 (real Step Functions state machine — no Pass placeholders, governed tasks + waitForTaskToken gate + controlled SQS outbox, in BOTH the SAM golden path and the nested agent-service.yaml) is also DONE. #6 (production-grade sandbox connector — `SandboxHttpConnector`: auth, idempotency, retries, timeouts, circuit breaker, reconciliation, lineage; `CONNECTOR_MODE=sandbox`) is also DONE. #8 (clean-account acceptance test + CI) is also DONE — `acceptance_test.sh` (live deploy→enforce→destroy), an offline contract test that statically proves the template encodes every control, and `.github/workflows/acceptance.yml` (always-on offline job + gated live job + supply-chain scans). **ALL P0 ITEMS COMPLETE.** P1 next: enterprise IdP federation, fail-closed PHI ml hook, README capability matrix.

**Recommended first execution slice (P0 #1–#3, #8):** reviewer service + bound-approval enforcement + durable replay + DynamoDB-backed audit + the failing-on-purpose acceptance tests. That single slice converts the three CISO-blocking findings from "modeled" to "enforced and proven."
