# Remediation — Round 2 (second external assessment)

**Headline:** the second assessment is **partly stale and partly correct**, and the single biggest
reason the score didn't move is almost certainly that **our Round-1 P0 work is not visible to the
reviewer** — it quotes code we already deleted (`self._seen_jti: set = set()`, the `Pass` states),
and 6 files including the entire acceptance/CI slice are **uncommitted** (`git status`). Step 0 below
is therefore "commit + push," and it likely recovers most of the gains already earned.

This doc maps each of the 9 findings to the **verified current state** of the tree, then gives a
prioritized build order to reach **75–80/100**.

## Finding-by-finding, against the current code

| # | Finding | Verified status now | Evidence |
|---|---------|---------------------|----------|
| 1 | Approval bypass + in-process jti set | **FIXED (golden path)** — reviewer quoted old code | `gateway.py` uses `self._jti_store` (default `InMemoryJtiStore`, prod `DynamoDBJtiStore`), `AUTH_REQUIRE_BOUND_APPROVAL=1` rejects the demo path; `reviewer.py` is a deployed authenticated service. The `_seen_jti` line no longer exists. |
| 2 | Audit sink not wired; chain in memory; no WORM export | **PARTIAL** | `index.py` DOES wire `GatewayAuditLog(sink=DynamoDBAppendOnlySink(AUDIT_TABLE))`. STILL OPEN: `DynamoDBAppendOnlySink` keeps `_last_hash` in process memory (not concurrency-safe); golden path has **no S3 Object-Lock bucket / no exporter**. → **Item A** |
| 3 | Full connector is an echo placeholder | **PARTIAL** | Golden path routes through the gateway to the fixture/sandbox connector (real framework + resilient `SandboxHttpConnector`). STILL OPEN: the **nested** `infra/cloudformation/connectors.yaml` Lambda is still `echo` + `TODO`. → **Item B** |
| 4 | Workflow is a Pass skeleton | **FIXED** — reviewer stale | `grep -c '"Type": "Pass"'` = **0** in both `golden-path/template.yaml` and `cloudformation/agent-service.yaml`; both have real Task states + `waitForTaskToken`. |
| 5 | Private networking not enforced | **PARTIAL** | Golden path: private subnets, **no IGW/NAT**, `VpcConfig` on every fn, interface+gateway endpoints, `/egress-check` probe. STILL OPEN: the **nested** `network.yaml` keeps NAT + `0.0.0.0/0` and `connectors.yaml` isn't VPC-attached. → **Item B** |
| 6 | Enterprise federation not deployed | **OPEN** | No `AWS::Cognito::UserPoolIdentityProvider` anywhere. → **Item C** |
| 7 | AgentCore target missing ToolSchema | **OPEN** | `agentcore-gateway.yaml` has `Mcp.Lambda.LambdaArn`, no `ToolSchema`. → **Item D** |
| 8 | PHI masking has a fail-open ML path | **OPEN** | `phi.py` `_ml_mask` `except Exception: return text`. → **Item E** |
| 9 | CI doesn't prove deployability | **PARTIAL** | Added `acceptance.yml`: offline **contract test** (template encodes the controls) + **gated live** deploy→enforce→destroy job + supply-chain (gitleaks/bandit/pip-audit/checkov/SBOM). STILL OPEN: live job needs an AWS OIDC account to actually run; no `terraform validate/plan`, container scan, signed releases, rollback/DR. → **Item F** |

**Net:** 2 fully fixed (already), 4 partial (golden path done, nested/durability open), 3 open. The
reviewer is largely scoring the **nested `infra/cloudformation/` quickstart** and a **pre-fix
snapshot**, not the hardened golden path.

## The one strategic decision

The golden path is the canonical, supported, tested Agent 01. The nested `infra/cloudformation/`
"full-suite quickstart" is where the reviewer's placeholder findings live. Two honest options:
- **(Recommended) Make the golden path THE quickstart** in the README, and either upgrade or clearly
  relabel the nested stack as "advanced/alternative reference (not the supported deploy)."
- **Or** bring the nested stack up to the golden-path bar (Item B). Higher effort, more surface.

Either way, **Item B's real work** (real connector dispatch + VPC isolation) must exist on whatever
path the README calls "the quickstart."

## Build order to 75–80 (mapped to the reviewer's own score table; baseline 60)

| Step | Work | Gain | Runs/verifies here? |
|------|------|------|---------------------|
| **0** | **Commit + push** slices #1–5 (6 uncommitted files) so the reviewer sees current state | recovers much of the "unchanged" 60 | user action (git is yours) |
| **A** | Concurrency-safe audit + **auto WORM export** (golden path: S3 Object-Lock bucket + DynamoDB Streams → exporter Lambda; per-record self-verifying sequence) | +4 | code+cfn-lint+unit tests ✔ |
| **B** | Nested quickstart to bar: real connector dispatch in `connectors.yaml`, VPC-attach + drop NAT/`0.0.0.0/0` in `network.yaml`, wire audit/jti envs — **or** relabel + point quickstart at golden path | +7 +3 | cfn-lint ✔ (live deploy needs account) |
| **C** | Enterprise **SAML/OIDC** `UserPoolIdentityProvider` + attribute/group→role mapping (golden path, optional via param) | +2 | cfn-lint ✔ |
| **D** | AgentCore **ToolSchema** + auth policy on the gateway target (or mark experimental) | +2 | cfn-lint ✔ |
| **E** | PHI ML hook **fail-closed** (drop record + security metric; never return unmasked) | hygiene | unit test ✔ |
| **F** | CI depth: `terraform validate/plan`, container scan, signed releases (cosign), rollback/DR test; wire the **live** acceptance job to a sandbox account | +4 +3 | partial here; live needs account |
| **G** | README **capability-status matrix** + maturity taxonomy so fixed controls stop being mis-scored | credibility | doc ✔ |

**To clear 75–80:** Step 0 + A + B + G is the high-leverage core; C, D, E, F push toward the mid-80s.
Items A–E and G are implementable and verifiable in-repo now (cfn-lint + unit tests, no AWS account);
the live-deploy portions of B and F require a sandbox account + OIDC and are already structured to run
on `workflow_dispatch`.
