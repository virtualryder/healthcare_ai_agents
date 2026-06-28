# HCOS Deepening Plan — to match/exceed the SLG bar

Benchmarked against `slg-ai-agents`. Goal: an AWS SA can take this to a customer, deploy it via
CloudFormation, and answer every CISO/CIO question — with the depth (security, GTM, platform)
of the SLG suite. Eight waves; each ends green (tests + lint + parse).

| Wave | What | Why (gap vs SLG) |
|---|---|---|
| **W1** | Harden `platform_core`: cryptographic JWT verification, **bound single-use separation-of-duties approvals**, enforced append-only audit sinks + negative-case tests | SLG control plane is cryptographically hardened; HCOS used simple claim/approval checks |
| **W2** | **Security package**: `SECURITY.md`, `THREAT-MODEL`, `NIST-800-53-CONTROL-MATRIX`, `OWASP-LLM-ATLAS-MAPPING`, `INCIDENT-RESPONSE-AND-KEY-MANAGEMENT`, `PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY` | "Call out each security issue and how it's met" — assessor-grade |
| **W3** | **Care & Claims Orchestration Platform** (`care_platform/`): governed-tool contract, canonical data, consent ledger (42 CFR Part 2), durable **saga + compensation**, compliance event bus, care/claims **journeys** | SLG ships a Whole-of-Government orchestration platform; HCOS had only an A2A supervisor |
| **W4** | **CI** (`.github/workflows/ci.yml`) + `CHANGELOG`, `VERSION`, root `SOURCES.md`, `IMPROVEMENTS-OVER-SLG.md` | SLG has CI + repo hygiene + positioning doc |
| **W5** | Decks: **AWS brand mark on every slide**, a platform deck, one-pager **leave-behinds** | User asked for the AWS logo; SLG has a platform deck + leave-behinds |
| **W6** | GTM depth: **SA field guide** (w/ CISO security-review checklist), platform GTM story, **deliverables/agent-handbooks**, deployment-models, future-use-cases, AWS-account-prereqs | SLG GTM is broader |
| **W7** | **Thorough README** (need → agents+cited gains+evidence tiers → security architecture → CIO/CISO/Architect Q&A → production-readiness+RACI → repo map) + per-agent `DEPLOY-RUNBOOK.md` | User wants a very thorough README answering CISO/CIO |
| **W8** | Final verification (tests + cfn-lint + HCL + ASL + decks + CI lint + link sweep) | Everything green |

Evidence-tier convention for all cited figures: **[GOV] / [PEER-REVIEWED] / [INDUSTRY-RESEARCH] /
[ASSOCIATION] / [SECTOR-PRESS] / [VENDOR-REPORTED] / [MODELED]** — sourced in `gtm/HPP-DECK-SOURCES.md`
and root `SOURCES.md`.
