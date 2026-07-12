# HPP AI Agent Suite — Status & Changelog

## Current state (June 2026)
- **platform_core/hpp_agent_platform** — built & tested: MCP authorization gateway
  (deny-by-default + least-privilege intersection + HITL + scoped tokens + PHI-masked
  append-only audit), PHI masker (HIPAA Safe Harbor), provider-abstracted LLM factory
  (**Bedrock default** + Guardrails; external Anthropic API gated behind `ALLOW_EXTERNAL_LLM=1`,
  non-PHI/dev only), connector framework (14 system kinds, fixture/live),
  A2A supervisor.
- **governance** — built & tested: grounding, prompt registry + manifest, eval harness +
  golden artifacts, red team, fairness (four-fifths), accessibility + health literacy,
  control mappings.
- **Agent 01 — Revenue-Cycle & Denial** — built to reference depth: LangGraph workflow with
  framework-enforced HITL interrupt, framework-free runner, gateway-backed tools, fixtures,
  Streamlit dashboard, AgentCore `/invocations`+`/ping` serve contract, Dockerfile, demo +
  live-path runbook, four-document doc set, full test suite.
- **infra/cloudformation (Agent 01)** — built & validated: quickstart master nesting network (VPC + in-account Bedrock endpoint + Flow Logs), security (KMS + Bedrock Guardrail with PHI filters + Cognito `hpp_role` + least-privilege role), data (append-only audit + HITL + WORM Object Lock), connectors Lambda, dual MCP gateway (portable API Gateway+Cognito JWT — the supported path; the AgentCore variant is **experimental — incomplete**, missing per-tool `ToolSchema`), and agent-service (Step Functions waitForTaskToken HITL | Fargate). **8 templates pass cfn-lint clean.** Plus `scripts/deploy.sh` + `build_lambdas.sh`.
- **Agent 02 — Prior-Authorization** — built to reference depth: requirement check (Da Vinci
  CRD), evidence assembly, MCG/InterQual criteria evaluation, grounded rationale, framework-
  enforced HITL before submission, monitor/escalate, full test suite + 4-doc set + live runbook.
  `payer.issue_determination` withheld from all agents.
- **Agent 03 — Clinical-Administration** — built to reference depth: chart load (FHIR) + care plan, 42 CFR Part 2 consent gate, task-typed artifact (summary/visit-prep/referral/discharge/inbox), grounding + PHI + health-literacy checks, framework-enforced clinician sign-off gate, full test suite + 4-doc set + live runbook. `ehr.draft_note` is a gated draft; no order-entry/signing.
- **Agent 04 — Patient Access** — built to reference depth: identity-gated benefits (270/271), deterministic Good Faith Estimate (No Surprises Act), scheduling availability, plain-language member message, framework-enforced rep gate, gated book+register writes; inactive-coverage escalation; full test suite + 4-doc set + live runbook.
- **Agent 05 — Utilization Management** — built to reference depth (first payer-side agent): MCG/InterQual criteria, coverage (LCD/NCD), four-fifths fairness screen, criteria-grounded recommendation (MEETS/DOES_NOT_MEET/NEEDS_INFO), framework-enforced medical-director gate. `payer.issue_determination` withheld from every agent; an adverse recommendation is forwarded, never auto-denied. Full test suite + 4-doc set + live runbook.
- **Agent 06 — Payment Integrity & Coding** — built to reference depth: code suggestion + NCCI/MUE validation + LCD/NCD necessity + 837 scrub; deterministic detection of upcoding/overpayment, bundling edits, duplicates, and unsupported necessity; framework-enforced reviewer gate. The agent FLAGS only — no recoupment, payment adjustment, or claim submission (submit_claim withheld). Full test suite + 4-doc set + live runbook.
- **Agent 07 — Care Management & Population Health** — built to reference depth: care-gap identification + HCC/RAF risk + SDOH, four-fifths fairness screen on risk strat, 42 CFR Part 2 consent gate, plain-language patient outreach, framework-enforced care-manager sign-off, gated care-plan write. Full test suite + 4-doc set + live runbook.
- **Agent 08 — Contact Center / Member Services** — built to reference depth (completes the suite): Amazon Connect member inquiries, claim status (276/277) + eligibility (270/271), identity gate before disclosure, plain-language responses, grievance intake, framework-enforced rep gate, gated log/grievance writes. Cannot submit an appeal (hands off to Agent 01). Full test suite + 4-doc set + live runbook.

**ALL 8 AGENTS BUILT.** CloudFormation stamped for all 8 (params CIDRs 10.30–10.37).

## Test status
**270 tests green as of 2026-07-10** (no API key). The per-suite breakdown below is the last recorded
snapshot, from the **2026-07-07** run of 185 (each agent's graph test skips if `langgraph` is not installed — 177 passed + 8 skipped without it). Adds control-plane negative-case tests (JWT verification, bound SoD approvals, audit hash chain), the orchestration-platform journey tests, the golden-path workflow tests, and the all-prompts-pinned test to the original 121.

Each agent is an independent deployable (own top-level `agent`/`tools` packages), so the
runner tests agents in separate pytest invocations: `bash scripts/run_tests.sh`.
Per-suite counts from the 2026-07-07 run:
```
platform_core/tests + governance — gateway authz/HITL, PHI masking, connectors, SECURITY control-plane, grounding, fairness, accessibility, red team, prompts (66)
care_platform         — saga+compensation, journeys, consent, authority-never-widens   (7)
golden-path workflow (Agent 01) — infra/golden-path-01-revenue-cycle/tests            (17)
01-revenue-cycle-...  — denial classification, appeal grounding, HITL submission     (15)
02-prior-authorization — requirement check, criteria grounding, gated submit, urgent (12)
03-clinical-administration — chart-grounded draft, consent/Part 2, clinician sign-off (11)
04-patient-access     — identity gate, GFE estimate, eligibility, gated book+register (12)
05-utilization-management — criteria, fairness screen, recommendation, director gate, withheld determination (10)
06-payment-integrity-coding — NCCI/MUE, upcoding/duplicate/necessity flags, reviewer gate, flag-only (12)
07-care-management-pophealth — gaps/risk/SDOH, fairness screen, Part 2 consent, care-manager gate (11)
08-contact-center-member-services — identity gate, claim/benefits/grievance, rep gate (12)
```

## Built (suite + GTM + ops layer all complete)
- ✅ All 8 agents to reference depth · platform_core · governance.
- ✅ `infra/cloudformation` — 8 templates (cfn-lint clean) + per-agent params (CIDRs 10.30–10.37).
- ✅ `infra/terraform` — module parity (network/security/data/connectors/gateway/agent-service) + per-agent tfvars.
- ✅ `aws-native-reference` — per-agent Step Functions ASL with `waitForTaskToken` HITL gate.
- ✅ `gtm` + `decks` — 11 professional decks (8 per-agent + executive + CISO/CMIO + orchestration platform), an optional logo (internal-track only), leave-behind one-pagers, cited `HPP-DECK-SOURCES.md`, demo storyboard, seller cheatsheet, live-formula `roi-calculator/`.
- ✅ `offerings` (11 docs) · `runbooks` (5) · `docs` (8: architecture, deploy-quickstart, WAF review, control mappings, briefings…).
- ✅ `GETTING-STARTED.md`, `Makefile`, `CONTRIBUTING.md`; per-agent prompt-registry test.
- ✅ **Hardened control plane** (JWT verify, bound SoD approvals, hash-chained audit) + security package (SECURITY.md + threat model + NIST 800-53 + OWASP-LLM/ATLAS + IR/key-mgmt).
- ✅ **Care & Claims Orchestration Platform** (`care_platform/`) — saga + compensation + consent + events + journeys.
- ✅ **One-command SAM golden path** (`infra/golden-path-01-revenue-cycle/`: build/smoke/teardown) + **reference live connector** (Agent 01 `demo/demo_live.py` over real HTTP).
- ✅ CI (`.github/workflows/ci.yml`), CHANGELOG, VERSION, SOURCES.md; 8 **agent-handbook PDFs** in `deliverables/`.

## What remains = the engagement (not code)
Production-readiness per customer: CSV/CSA validation, enterprise IdP integration + role mapping,
live-connector validation (Epic/Oracle Health, Change Healthcare/Availity, payer FHIR/X12),
Bedrock Guardrail tuning, penetration test, HITRUST/SOC 2 evidence assembly.

## Changelog
- **2026-06-25** — Initial foundation: platform_core, governance, flagship Agent 01,
  suite docs, agent 02–08 specs. 38 tests green.

- **2026-06-25** — CloudFormation infra for Agent 01 (8 templates, cfn-lint clean) + deploy scripts.
- **2026-06-25** — Agent 02 (Prior-Authorization) built to reference depth; 51 tests green across suites; added scripts/run_tests.sh.
- **2026-06-25** — Stamped out CloudFormation for Agent 02 (per-agent params + non-overlapping VpcCidr wired through quickstart + deploy.sh). cfn-lint clean.
- **2026-06-25** — Agent 03 (Clinical-Administration) built to reference depth; 62 tests green across suites.
- **2026-06-25** — Stamped out CloudFormation for Agent 03 (params + VpcCidr 10.32.0.0/16). cfn-lint clean.
- **2026-06-25** — Agent 04 (Patient Access) built to reference depth; 74 tests green across suites.
- **2026-06-25** — Stamped out CloudFormation for Agent 04 (params + VpcCidr 10.33.0.0/16). cfn-lint clean.
- **2026-06-25** — Agent 05 (Utilization Management) built to reference depth; 84 tests green across suites.
- **2026-06-25** — Stamped out CloudFormation for Agent 05 (params + VpcCidr 10.34.0.0/16). cfn-lint clean.
- **2026-06-25** — Agent 06 (Payment Integrity- **2026-06-26** — GTM + ops layer complete: Terraform parity (8 .tf modules), AWS-native Step Functions ASL (8), 10 professional decks + ROI calculator (xlsx) reframed per agent with recent cited data in the reference deck format, offerings (11), runbooks (5), docs (8). Polish: GETTING-STARTED + Makefile + CONTRIBUTING, per-agent prompt-pinning test, deploy quickstart with local-first + troubleshooting. **121 tests green; cfn-lint + HCL + ASL + decks all validate.**
- **2026-06-26** — Depth pass to/beyond the SLG bar: hardened control plane (JWT verify, bound SoD approvals, hash-chained audit) + 14 negative-case tests; security package (6 docs); Care & Claims Orchestration Platform (saga+compensation+consent+events, 7 tests); CI (.github/workflows); CHANGELOG/VERSION/SOURCES; AWS-brand decks + platform deck + leave-behinds; SA field guide + platform GTM + 8 agent handbooks + deployment-models/future-use-cases/account-prereqs; assessor-grade README + 8 deploy runbooks. **144 tests green; cfn-lint + HCL + ASL + CI all validate.**
- **2026-06-26** — One-command SAM golden path (Agent 01) + reference live connector (real HTTP façade, demo_live.py + 2 tests) + agent-handbook PDFs + README refresh. **144 tests green.**
- **2026-07-10** — Hardening + honesty pass: audit immutability enforced in the golden-path IAM (conditional `PutItem`, `UpdateItem` scoped to the `__seq__` counter, `DeleteItem` denied) with the **audit and approval signing secrets split** (`AUDIT_SIGNING_SECRET` vs `APPROVAL_SIGNING_SECRET`); agents 03–08 dead `if _demo() or True` branch removed — they now fail loud in live mode as deterministic reference workflows (01/02 hold the real LLM path); `tools/check_maturity.py` + `governance/tests/test_no_status_drift.py` drift gate; real-data PHI masking made fail-closed under `ALLOW_REAL_DATA` (regex does not mask patient names — NER mandatory in real-data mode); pinned lockfiles (`requirements-lock.txt` + `requirements-dev.txt`) with **blocking pip-audit**; **LLM provider defaults to Bedrock**, external Anthropic API gated behind `ALLOW_EXTERNAL_LLM=1`. **270 tests green.**
