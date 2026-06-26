# HPP AI Agent Suite — Status & Changelog

## Current state (June 2026)
- **platform_core/hpp_agent_platform** — built & tested: MCP authorization gateway
  (deny-by-default + least-privilege intersection + HITL + scoped tokens + PHI-masked
  append-only audit), PHI masker (HIPAA Safe Harbor), provider-abstracted LLM factory
  (Anthropic / Bedrock + Guardrails), connector framework (14 system kinds, fixture/live),
  A2A supervisor.
- **governance** — built & tested: grounding, prompt registry + manifest, eval harness +
  golden artifacts, red team, fairness (four-fifths), accessibility + health literacy,
  control mappings.
- **Agent 01 — Revenue-Cycle & Denial** — built to reference depth: LangGraph workflow with
  framework-enforced HITL interrupt, framework-free runner, gateway-backed tools, fixtures,
  Streamlit dashboard, AgentCore `/invocations`+`/ping` serve contract, Dockerfile, demo +
  live-path runbook, four-document doc set, full test suite.
- **infra/cloudformation (Agent 01)** — built & validated: quickstart master nesting network (VPC + in-account Bedrock endpoint + Flow Logs), security (KMS + Bedrock Guardrail with PHI filters + Cognito `hpp_role` + least-privilege role), data (append-only audit + HITL + WORM Object Lock), connectors Lambda, dual MCP gateway (portable API Gateway+Cognito JWT / AgentCore), and agent-service (Step Functions waitForTaskToken HITL | Fargate). **8 templates pass cfn-lint clean.** Plus `scripts/deploy.sh` + `build_lambdas.sh`.
- **Agent 02 — Prior-Authorization** — built to reference depth: requirement check (Da Vinci
  CRD), evidence assembly, MCG/InterQual criteria evaluation, grounded rationale, framework-
  enforced HITL before submission, monitor/escalate, full test suite + 4-doc set + live runbook.
  `payer.issue_determination` withheld from all agents.
- **Agent 03 — Clinical-Administration** — built to reference depth: chart load (FHIR) + care plan, 42 CFR Part 2 consent gate, task-typed artifact (summary/visit-prep/referral/discharge/inbox), grounding + PHI + health-literacy checks, framework-enforced clinician sign-off gate, full test suite + 4-doc set + live runbook. `ehr.draft_note` is a gated draft; no order-entry/signing.
- **Agent 04 — Patient Access** — built to reference depth: identity-gated benefits (270/271), deterministic Good Faith Estimate (No Surprises Act), scheduling availability, plain-language member message, framework-enforced rep gate, gated book+register writes; inactive-coverage escalation; full test suite + 4-doc set + live runbook.
- **Agent 05 — Utilization Management** — built to reference depth (first payer-side agent): MCG/InterQual criteria, coverage (LCD/NCD), four-fifths fairness screen, criteria-grounded recommendation (MEETS/DOES_NOT_MEET/NEEDS_INFO), framework-enforced medical-director gate. `payer.issue_determination` withheld from every agent; an adverse recommendation is forwarded, never auto-denied. Full test suite + 4-doc set + live runbook.
- **Agent 06 — Payment Integrity & Coding** — built to reference depth: code suggestion + NCCI/MUE validation + LCD/NCD necessity + 837 scrub; deterministic detection of upcoding/overpayment, bundling edits, duplicates, and unsupported necessity; framework-enforced reviewer gate. The agent FLAGS only — no recoupment, payment adjustment, or claim submission (submit_claim withheld). Full test suite + 4-doc set + live runbook.
- **Agent 07 — Care Management & Population Health** — built to reference depth: care-gap identification + HCC/RAF risk + SDOH, four-fifths fairness screen on risk strat, 42 CFR Part 2 consent gate, plain-language patient outreach, framework-enforced care-manager sign-off, gated care-plan write. Full test suite + 4-doc set + live runbook.
- **Agent 08** — Documented: per-agent spec README and scaffold; build follows the 01–07 pattern.

## Test status
`107 passed across suites` (the skip is the LangGraph graph-wiring test when langgraph is not
installed; it passes when it is). All run with **no API key**.

Each agent is an independent deployable (own top-level `agent`/`tools` packages), so the
runner tests agents in separate pytest invocations: `bash scripts/run_tests.sh`.
```
platform_core/tests   — gateway authz/HITL, PHI masking, connectors      (16)
governance            — grounding, fairness, accessibility, HITL, red team, prompts (12)
01-revenue-cycle-...  — denial classification, appeal grounding, HITL submission     (11)
02-prior-authorization — requirement check, criteria grounding, gated submit, urgent (12)
03-clinical-administration — chart-grounded draft, consent/Part 2, clinician sign-off (11)
04-patient-access     — identity gate, GFE estimate, eligibility, gated book+register (12)
05-utilization-management — criteria, fairness screen, recommendation, director gate, withheld determination (10)
06-payment-integrity-coding — NCCI/MUE, upcoding/duplicate/necessity flags, reviewer gate, flag-only (12)
07-care-management-pophealth — gaps/risk/SDOH, fairness screen, Part 2 consent, care-manager gate (11)
```

## Roadmap (next passes)
1. Build agents 03–08 to Demonstrated depth (same scaffold).
2. `infra/cloudformation` (network, security+Guardrail, append-only audit/WORM, connector
   Lambdas, two gateway modes, agent service) + Terraform parity.
3. `aws-native-reference` (Strands + Step Functions `waitForTaskToken` rebuilds).
4. `gtm` decks (per-agent + executive overview + CISO/CMIO adoption review) from the cited
   `HPP-DECK-SOURCES.md`; `roi-calculator` workbook.
5. `offerings` (POC, pilot, SOW, battlecard, TCO/ROI, TPRM) and `runbooks`.

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
- **2026-06-25** — Agent 06 (Payment Integrity & Coding) built to reference depth; 96 tests green across suites.
- **2026-06-25** — Stamped out CloudFormation for Agent 06 (params + VpcCidr 10.35.0.0/16). cfn-lint clean.
- **2026-06-25** — Agent 07 (Care Management & Population Health) built to reference depth; 107 tests green across suites.
