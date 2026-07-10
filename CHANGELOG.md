# Changelog

All notable changes to the HPP AI Agent Suite. Pre-1.0 reference accelerator; only the latest
`main` is supported.

## [Unreleased] — 2026-07-10 — Hardening & honesty pass
### Security
- **Audit immutability enforced** in the golden-path template (`infra/golden-path-01-revenue-cycle/template.yaml`):
  conditional `PutItem`, IAM scoping `UpdateItem` to the atomic `__seq__` counter only, and an explicit
  `DeleteItem` **Deny** — the append-only, hash-chained audit can no longer be rewritten or deleted at runtime.
- **Audit and approval signing secrets split** — the audit chain is sealed with a dedicated
  `AUDIT_SIGNING_SECRET`, separate from `APPROVAL_SIGNING_SECRET`, so an approval-key compromise cannot
  forge audit entries (`audit_sinks.py`, `approvals.py`).
- **LLM provider now defaults to in-account Amazon Bedrock** (`LLM_PROVIDER=bedrock`). The external
  Anthropic API is gated behind an explicit `ALLOW_EXTERNAL_LLM=1` opt-in (non-PHI/dev only), so a bare
  `LLM_PROVIDER` flip can no longer silently egress PHI off AWS (`llm_factory.py`).
- **Real-data PHI masking is fail-closed** under `ALLOW_REAL_DATA`: the deterministic regex pass does not
  mask free-text patient names (HIPAA Safe Harbor #1), so the NER engine is **mandatory** in real-data mode.
### Supply chain / CI
- **Pinned lockfiles** (`requirements-lock.txt` runtime + `requirements-dev.txt` tooling); **pip-audit is now
  a blocking CI gate** (dropped `|| true`) — a known-vulnerable pinned dependency fails the build.
- `tools/check_maturity.py` + `governance/tests/test_no_status_drift.py` — a **status-drift gate** that fails
  CI if any current-state doc cites a test count that disagrees with `MATURITY.yaml` (now 263).
### Changed
- **Agents 03–08 dead `if _demo() or True` branch removed** — they now fail loud in live mode. They are
  **deterministic reference workflows**; agents 01/02 carry the real LLM path.
- Docs synced to the above; `MATURITY.yaml` test counts regenerated to **263**.

## [0.2.0] — 2026-06-26 — Depth pass (to/beyond the SLG bar)
### Added
- **Hardened control plane:** cryptographic RS256/JWKS JWT verification with alg-confusion guard
  (`jwt_verify.py`); **bound, single-use, separation-of-duties** approval tokens (`approvals.py`);
  append-only **hash-chained** audit + WORM sink abstraction (`audit_sinks.py`, `audit.py`).
  14 control-plane negative-case tests (JWT, approvals, audit chain).
- **Security package:** `SECURITY.md`, `docs/THREAT-MODEL.md`, `docs/NIST-800-53-CONTROL-MATRIX.md`,
  `docs/OWASP-LLM-ATLAS-MAPPING.md`, `docs/INCIDENT-RESPONSE-AND-KEY-MANAGEMENT.md`,
  `docs/PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`.
- **Care & Claims Orchestration Platform** (`care_platform/`): governed-action contract, canonical
  record, AAL-gated consent ledger (42 CFR Part 2), durable saga with compensation, compliance
  event bus, three cross-agent journeys + `aws-native-reference/care-platform/` runner. 7 tests.
- **CI** (`.github/workflows/ci.yml`): tests + security + IaC lint. `CHANGELOG.md`, `VERSION`,
  root `SOURCES.md`.
- **GTM/decks:** an optional logo (internal-track only) on every deck; platform deck; leave-behind one-pagers; SA field
  guide; per-agent deployment handbooks (planned in this pass).

## [0.1.0] — 2026-06-25 — Initial suite
- All 8 agents to reference depth; `platform_core`; `governance`; CloudFormation (8, cfn-lint clean)
  + Terraform parity; AWS-native Step Functions rebuilds; GTM decks + ROI calculator; offerings;
  runbooks; docs. 121 tests green, no API key.

### Added (continued)
- One-command **SAM golden path** (`infra/golden-path-01-revenue-cycle/`) with smoke test + teardown.
- **Reference live connector** — runnable HTTP/FHIR fa\xc3\xa7ade + Agent 01 `demo_live.py` (real HTTP path, no API key) + 2 tests.
- Agent-handbook **PDFs** in `deliverables/agent-handbooks/`.
