# Changelog

All notable changes to the HPP AI Agent Suite. Pre-1.0 reference accelerator; only the latest
`main` is supported.

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
