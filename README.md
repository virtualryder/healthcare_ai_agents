# HPP AI Agent Suite

### Governed AI Agents for Health Providers & Plans — Built on AWS

![Tests](https://img.shields.io/badge/tests-121%20passing-brightgreen)
![Agents](https://img.shields.io/badge/agents-8%2F8%20built-brightgreen)
![CloudFormation](https://img.shields.io/badge/cfn--lint-passing-brightgreen)
![Terraform](https://img.shields.io/badge/terraform-parity-brightgreen)
![Maturity](https://img.shields.io/badge/maturity-Demonstrated%20%2B%20Deployable-orange)
![HIPAA](https://img.shields.io/badge/HIPAA-BAA%20Required-red)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-proprietary-blue)

> **The agents are not the product. The governed platform that makes them deployable, auditable, and HIPAA-defensible is.**

---

## Status at a Glance

All **8 agents are built to Demonstrated + Deployable-by-design** — working code, tests,
docs, CloudFormation + Terraform templates, Step Functions rebuilds, and live Bedrock paths.
**Production-readiness** (CSV/CSA, IdP integration, live-connector validation, penetration
test, HITRUST) **is the engagement, not a day-one deliverable.**

See [`SUITE-STATUS.md`](SUITE-STATUS.md) for the full feature matrix, test count breakdown,
and changelog.

---

## Quick Navigation

| I want to... | Start here |
|---|---|
| Run a demo on my laptop (no AWS, no API key) | [`GETTING-STARTED.md`](GETTING-STARTED.md) Step 1 |
| Understand the architecture | [`docs/SUITE-ARCHITECTURE.md`](docs/SUITE-ARCHITECTURE.md) |
| Deploy to AWS (CloudFormation) | [`docs/DEPLOY-QUICKSTART.md`](docs/DEPLOY-QUICKSTART.md) |
| Deploy to AWS (Terraform) | [`infra/terraform/README.md`](infra/terraform/README.md) |
| See what's built and what's not | [`SUITE-STATUS.md`](SUITE-STATUS.md) |
| Understand the governance controls | [`governance/README.md`](governance/README.md) |
| Review compliance & control mappings | [`docs/COMPLIANCE-CONTROL-MAPPINGS.md`](docs/COMPLIANCE-CONTROL-MAPPINGS.md) |
| Review the shared responsibility model | [`docs/SHARED-RESPONSIBILITY-MATRIX.md`](docs/SHARED-RESPONSIBILITY-MATRIX.md) |
| Run the full test suite (121 tests, no API key) | `make test` or `bash scripts/run_tests.sh` |
| Build an AWS-native (Step Functions) variant | [`aws-native-reference/README.md`](aws-native-reference/README.md) |
| Understand why the MCP layer exists | [`docs/WHY-THE-MCP-LAYER.md`](docs/WHY-THE-MCP-LAYER.md) |
| See the pitch decks | [`decks/README.md`](decks/README.md) |
| Sell this to a customer | [`SOLUTION-FIELD-GUIDE.md`](SOLUTION-FIELD-GUIDE.md) & [`offerings/`](offerings/) |
| Run operational playbooks | [`runbooks/README.md`](runbooks/README.md) |
| Contribute code | [`CONTRIBUTING.md`](CONTRIBUTING.md) |

---

## Documentation by Role

| Role | Read first | Then explore |
|---|---|---|
| **Solution Architect / CTO** | [`README.md`](README.md) · [`docs/SUITE-ARCHITECTURE.md`](docs/SUITE-ARCHITECTURE.md) | [`ENTERPRISE-PLATFORM.md`](ENTERPRISE-PLATFORM.md) · [`docs/WELL-ARCHITECTED-REVIEW.md`](docs/WELL-ARCHITECTED-REVIEW.md) · [`docs/WHY-THE-MCP-LAYER.md`](docs/WHY-THE-MCP-LAYER.md) |
| **DevOps / Platform Engineer** | [`GETTING-STARTED.md`](GETTING-STARTED.md) · [`docs/DEPLOY-QUICKSTART.md`](docs/DEPLOY-QUICKSTART.md) | [`infra/cloudformation/README.md`](infra/cloudformation/README.md) · [`infra/terraform/README.md`](infra/terraform/README.md) · [`runbooks/README.md`](runbooks/README.md) |
| **Security / Compliance Officer** | [`docs/SHARED-RESPONSIBILITY-MATRIX.md`](docs/SHARED-RESPONSIBILITY-MATRIX.md) · [`docs/COMPLIANCE-CONTROL-MAPPINGS.md`](docs/COMPLIANCE-CONTROL-MAPPINGS.md) | [`governance/README.md`](governance/README.md) · [`docs/WELL-ARCHITECTED-REVIEW.md`](docs/WELL-ARCHITECTED-REVIEW.md) · [`docs/STAKEHOLDER-SECURITY-BRIEFINGS.md`](docs/STAKEHOLDER-SECURITY-BRIEFINGS.md) |
| **Sales Engineer / Solutions Consultant** | [`SOLUTION-FIELD-GUIDE.md`](SOLUTION-FIELD-GUIDE.md) · [`gtm/SELLER-FIRST-MEETING-CHEATSHEET.md`](gtm/SELLER-FIRST-MEETING-CHEATSHEET.md) | [`offerings/`](offerings/) · [`decks/README.md`](decks/README.md) · [`gtm/DEMO-STORYBOARD.md`](gtm/DEMO-STORYBOARD.md) |
| **Healthcare Domain Expert** | Agent-specific README (e.g., [`01-revenue-cycle-denial-agent/README.md`](01-revenue-cycle-denial-agent/README.md)) | Agent's `docs/` subdirectory · [`SOLUTION-FIELD-GUIDE.md`](SOLUTION-FIELD-GUIDE.md) |
| **Developer / Contributor** | [`GETTING-STARTED.md`](GETTING-STARTED.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) | [`governance/README.md`](governance/README.md) · agent-specific code |
| **Operator / On-call** | [`runbooks/README.md`](runbooks/README.md) | [Incident Response](runbooks/INCIDENT-RESPONSE.md) · [DR](runbooks/DR-RUNBOOK.md) · [HITL Queue](runbooks/HITL-QUEUE-OPERATIONS.md) · [Model Degradation](runbooks/MODEL-DEGRADATION-RESPONSE.md) |

---

## Who Should Use This

**Yes:**
- **Systems Integrators** deploying AI into healthcare organizations — you need the governance + audit compliance layer
- **Health Systems** (providers) piloting AI in revenue-cycle, clinical docs, or patient access workflows
- **Health Plans** (payers) piloting AI in prior-auth, UM, claims, or member services
- **AWS customers** with a HIPAA BAA and Bedrock access who want a reference accelerator
- **Architecture & Security teams** who want to see deny-by-default, HITL gates, and PHI masking in practice

**No:**
- **Off-the-shelf SaaS seekers** — this is a decision-support accelerator, not a certified product
- **Teams without AWS** — inference is tied to Anthropic API or Amazon Bedrock
- **Autonomous execution** — every consequential action (claim submission, coverage determination, note signature) requires human approval

---

## Quick Start

New here? **[`GETTING-STARTED.md`](GETTING-STARTED.md)** is the front door — prove the
flagship agent on your laptop with no API key, run the 121-test suite, then deploy into a
new AWS account.

```bash
# Install
make install                        # or: pip install -e platform_core && pip install langgraph streamlit

# Demo any agent (no API key)
make demo AGENT=01-revenue-cycle-denial   # or: cd 01-revenue-cycle-denial-agent && EXTRACT_MODE=demo python demo/demo_run.py

# Full test suite (121 tests, no API key)
make test                           # or: bash scripts/run_tests.sh

# Deploy to AWS
scripts/build_lambdas.sh 01-revenue-cycle-denial
scripts/deploy.sh 01-revenue-cycle-denial dev portable native s3://my-cfn-staging/hpp 10.30.0.0/16
# Or with Terraform: cd infra/terraform && terraform apply -var-file=envs/01-revenue-cycle-denial.tfvars
```

See [`docs/DEPLOY-QUICKSTART.md`](docs/DEPLOY-QUICKSTART.md) for the full deployment path.

---

## Positioning

| What this is | What this is not |
|---|---|
| A governed, auditable accelerator — bring your own LLM call without the compliance scaffolding and you still have a prototype | A certified, validated, production-ready SaaS product you can hand to a customer unchanged |
| Eight agents with shared platform controls that compound across the portfolio | Eight point tools built independently with no governance consistency |
| A reference for Amazon Bedrock AgentCore Gateway + Identity + Runtime semantics — testable locally, deployable on AWS | A vendor lock-in — the gateway semantics are replicated in `platform_core/` so the logic is readable and testable without an AWS account |
| Decision-support — drafts, assembles, monitors, flags — with humans owning every consequential decision (a determination, a submission, a signature) | Autonomous execution in clinical or coverage workflows |

---

## Maturity Ladder

Every agent and platform component is positioned honestly against four levels:

| Level | Description | What it means |
|---|---|---|
| **Documented** | Architecture, workflow, and compliance design are written and reviewed | Useful for discovery and architecture review; not runnable |
| **Demonstrated** | Code runs end-to-end in `EXTRACT_MODE=demo` (no API key, deterministic fixtures) | Proof of concept; suitable for internal demos and early customer workshops |
| **Deployable** | Container contract (ARM64, `/invocations`, `/ping`) and CI pass; requires customer AWS account and Bedrock access | Suitable for a customer pilot with SI-managed infrastructure |
| **Production-ready** | Customer computer-system validation (CSV/CSA), IdP integration, connectors tested against live systems, penetration test | Engagement milestone, not a day-one deliverable |

All eight agents are built to **Demonstrated + Deployable-by-design**. All eight ship
**CloudFormation + Terraform infra** (cfn-lint clean) and an **AWS-native Step Functions
rebuild** with a `waitForTaskToken` human gate.

---

## The Eight Agents

| # | Agent | Problem it solves | Primary systems | Key regulations |
|---|---|---|---|---|
| **01** | [Revenue-Cycle & Denial](01-revenue-cycle-denial-agent/README.md) | Denials reached ~11.8% and climbing; hospitals spent ~$18B in 2025 overturning them and 35–60% of denials are never reworked | Patient accounting, clearinghouse (X12 837/835/277), payer portal, encoder, EHR/FHIR | HIPAA, CMS-0057-F, No Surprises Act, False Claims Act |
| **02** | [Prior-Authorization](02-prior-authorization-agent/README.md) | ~39 PAs/physician/week (≈13 hrs); 94% say PA delays care; CMS mandates FHIR PA APIs by 2027 | Payer (Da Vinci CRD/DTR/PAS, X12 278), MCG/InterQual, EHR, IDP | CMS-0057-F, HIPAA, state PA-transparency laws |
| **03** | [Clinical-Administration](03-clinical-administration-agent/README.md) | Documentation and inbox burden drive clinician burnout; summaries and drafts compress it | EHR/FHIR (HealthLake, Comprehend Medical), care plan, scheduling, consent | HIPAA, 21st Century Cures, 42 CFR Part 2 |
| **04** | [Patient Access](04-patient-access-agent/README.md) | Access friction and registration errors drive leakage and downstream denials | Scheduling, registration, payer eligibility (270/271), identity | HIPAA, No Surprises Act, Section 1557 |
| **05** | [Utilization Management](05-utilization-management-agent/README.md) | UM is high-volume and under AI scrutiny; the determination must stay human | MCG/InterQual, LCD/NCD, payer, EHR | CMS AI-in-UM guidance, ERISA, NCQA, MH Parity |
| **06** | [Payment Integrity & Coding](06-payment-integrity-coding-agent/README.md) | Coding defects drive denials and FCA exposure; integrity recoveries are measurable | Encoder (NCCI/MUE, DRG), patient accounting, clearinghouse, EHR | HIPAA, CMS NCCI, False Claims Act, OIG |
| **07** | [Care Management & Pop Health](07-care-management-pophealth-agent/README.md) | Value-based programs depend on care-gap closure and accurate risk capture | Care management, EHR/FHIR, SDOH, consent | HIPAA, CMS risk-adjustment integrity, NCQA, Section 1557, 42 CFR Part 2 |
| **08** | [Contact Center / Member Services](08-contact-center-member-services-agent/README.md) | Member-service volume spikes around denials and benefits; grounded answers deflect it | Amazon Connect, payer (276/277, 270/271), identity, KB | HIPAA, Section 1557, TCPA |

Each agent includes: LangGraph workflow, governed tool access, deterministic fixtures, test
suite, Streamlit dashboard, four-document doc set (`docs/`), Dockerfile, demo, and a live
Bedrock/connector path.

---

## Shared Platform (`platform_core/hpp_agent_platform/`)

Every agent shares the same platform stack. Controls compound: a governance improvement to
the PHI masker, the grounding checker, or the audit trail benefits all eight agents at once.

### LLM Factory
Routes inference to **Anthropic Claude** (API) or **Amazon Bedrock** (in-account, under the
AWS BAA, no PHI egress) by deployment mode. `EXTRACT_MODE=demo` bypasses the LLM for local
testing. Bedrock Guardrails are mandatory in production (enforced in code).

### PHI Masking (`phi.py`)
Deterministic masking of HIPAA Safe Harbor identifiers (SSN, MRN, member/beneficiary ID,
claim/account numbers, dates, contact info, addresses, payment cards) at every log/audit
boundary. Code sets (ICD-10, CPT/HCPCS) and the NPI are preserved — they are non-PHI
reference data the agents must reason over.

### MCP Authorization Gateway (`mcp_gateway/`)
The governed front door. **No agent calls a vendor system directly.** Every tool call
passes one enforcement point: identity verification (fail-closed on missing subject);
**deny-by-default authorization with least-privilege intersection** —
`permitted(tool) ⇔ tool ∈ AGENT_TOOL_GRANTS[agent] ∩ ROLE_ENTITLEMENTS[user_roles]`, so an
agent can never exceed the human; a **human-approval gate** on high-risk writes; short-lived
**tool-scoped tokens** (no standing service accounts); and a **PHI-masked append-only audit**
with lineage to the system reached. This is the reference logic for Amazon Bedrock
AgentCore Gateway + Identity. Consequential authorities (`clearinghouse.submit_claim`,
`payer.issue_determination`) are deliberately withheld from agents and held only by human
roles.

### Connector Framework (`connectors/`)
One typed interface per system category (EHR, patient accounting, clearinghouse, payer,
coding, clinical criteria, care plan, scheduling, registration, KB, identity, consent, IDP,
contact center). Demo mode uses deterministic fixtures; live mode swaps in real adapters
behind identical signatures — no agent code changes.

---

## Governance Controls Matrix

Every control is enforced in code and verified by automated tests — no API key required.

| Control | Enforced by | Tested by | Status |
|---|---|---|---|
| **Deny-by-default authorization** | `mcp_gateway/policy.py` | `platform_core/tests/test_gateway.py` | Passing |
| **Least-privilege intersection** | `mcp_gateway/gateway.py` | Gateway authz tests | Passing |
| **HITL gate (high-risk writes)** | LangGraph `interrupt_before` / Step Functions `waitForTaskToken` | `governance/tests/test_hitl_enforced.py` | Passing |
| **PHI masking (Safe Harbor)** | `platform_core/hpp_agent_platform/phi.py` | `platform_core/tests/test_phi.py` | Passing |
| **Grounding verification** | `governance/grounding.py` | `governance/tests/test_grounding.py` | Passing |
| **Prompt version pinning** | `governance/prompt_manifest.json` | `governance/tests/test_prompt_registry.py` + `test_all_prompts_pinned.py` | Passing |
| **Red team (injection/exfil/bypass)** | `governance/redteam/scenarios.py` | `governance/tests/test_redteam.py` | Passing |
| **Fairness (four-fifths rule)** | `governance/fairness/disparate_impact.py` | `governance/tests/test_fairness.py` | Passing |
| **Accessibility (WCAG 2.1 AA)** | `governance/accessibility/wcag.py` | `governance/tests/test_accessibility.py` | Passing |
| **Control mappings** | `governance/controls/control_mappings.py` | Regime → control → AWS service | Reference |

See [`governance/README.md`](governance/README.md) for full details and
[`docs/COMPLIANCE-CONTROL-MAPPINGS.md`](docs/COMPLIANCE-CONTROL-MAPPINGS.md) for the
regime-level mapping (HIPAA, CMS-0057-F, No Surprises Act, Section 1557, 42 CFR Part 2).

---

## Infrastructure as Code

The suite ships with **two IaC options** for all 8 agents. Pick one; both achieve the same governed architecture.

### Option 1: CloudFormation (Quick-start)

```bash
scripts/build_lambdas.sh 01-revenue-cycle-denial
scripts/deploy.sh 01-revenue-cycle-denial dev portable native s3://my-cfn-staging/hpp 10.30.0.0/16
```

Master quickstart nests 7 stacks: network (VPC + Bedrock endpoint), security (KMS + Guardrail + Cognito), data (append-only audit + WORM Object Lock), connectors, dual gateway (portable + AgentCore), and agent-service (Step Functions HITL + Fargate). 8 templates pass cfn-lint clean. See [`infra/cloudformation/README.md`](infra/cloudformation/README.md).

### Option 2: Terraform (Modular)

```bash
cd infra/terraform
terraform init
terraform apply -var-file=envs/01-revenue-cycle-denial.tfvars
```

Six modules (network, security, data, connectors, gateway, agent-service) with per-agent tfvars. See [`infra/terraform/README.md`](infra/terraform/README.md).

### Deploy Mode: Container vs. Native

- **Container mode:** LangGraph runtime on ECS Fargate / AgentCore. Portable across clouds.
- **Native mode:** AWS Step Functions with `waitForTaskToken` HITL gates. AWS-only, deterministic state machine.

See [`aws-native-reference/README.md`](aws-native-reference/README.md) for per-agent Step Functions ASL definitions.

---

## AWS Service Choices

| Layer | Service | Why |
|---|---|---|
| **In-account inference** | Amazon Bedrock | HIPAA-eligible, no PHI egress, data stays in VPC under AWS BAA |
| **FHIR store** | Amazon HealthLake | Native FHIR R4, EHR interop |
| **Contact center** | Amazon Connect | Integrated voice + chat for member services agent |
| **Orchestration & HITL** | Step Functions + LangGraph | `waitForTaskToken` for named human gates; deterministic state machine |
| **Data integrity & audit** | DynamoDB + S3 Object Lock | Append-only (deny Update/Delete), WORM (7-year retention), PITR |
| **Encryption** | KMS CMK | Customer-managed keys for data at rest |
| **Access control** | Cognito + STS | Identity federation, short-lived tokens, role-based entitlements |
| **Guardrails** | Bedrock Guardrails | PII detection/masking, denied-topic filtering, grounding enforcement |
| **Document extraction** | Bedrock Data Automation | Clinical-document extraction (structured + unstructured) |

---

## Repository Structure

```
healthcare_ai_agents/
├── GETTING-STARTED.md                   # 3-step onboarding: demo → test → deploy
├── CONTRIBUTING.md                       # Conventions: agent isolation, no direct SDK calls, prompt pinning
├── SUITE-STATUS.md                       # Feature matrix, test count, changelog
├── ENTERPRISE-PLATFORM.md               # Deep architecture: ADR-001, orchestration, governed access layer
├── SOLUTION-FIELD-GUIDE.md              # Per-buyer pitches, qualification questions, land-and-expand
├── Makefile                              # Common tasks: install, test, demo, evals, lint, decks, roi
│
├── 01-revenue-cycle-denial-agent/       # Agent 01 — flagship (full depth + live path)
├── 02-prior-authorization-agent/        # Agent 02 — full depth (Demonstrated + Deployable)
├── 03-clinical-administration-agent/    # Agent 03 — full depth
├── 04-patient-access-agent/             # Agent 04 — full depth
├── 05-utilization-management-agent/     # Agent 05 — full depth
├── 06-payment-integrity-coding-agent/   # Agent 06 — full depth
├── 07-care-management-pophealth-agent/  # Agent 07 — full depth
├── 08-contact-center-member-services-agent/  # Agent 08 — full depth
│   └── (each agent: agent/ tools/ data/ demo/ docs/ tests/ Dockerfile app.py)
│
├── platform_core/                       # Shared platform: LLM factory, PHI masker, MCP gateway, connectors, A2A supervisor
├── governance/                          # Grounding, prompt registry, evals, red team, fairness, accessibility, control mappings
│
├── docs/                                # Suite-level documentation
│   ├── SUITE-ARCHITECTURE.md            #   Six-layer reference architecture and request path
│   ├── DEPLOY-QUICKSTART.md             #   Empty account → running governed agent
│   ├── COMPLIANCE-CONTROL-MAPPINGS.md   #   Regime → platform control → AWS service
│   ├── SHARED-RESPONSIBILITY-MATRIX.md  #   AWS / SI / Customer responsibility divide
│   ├── WELL-ARCHITECTED-REVIEW.md       #   AWS WAF review (all five pillars)
│   ├── STAKEHOLDER-SECURITY-BRIEFINGS.md #  CISO, CMIO, and compliance officer briefings
│   ├── WHY-THE-MCP-LAYER.md             #   Rationale for MCP gateway over direct LLM calls
│   └── AWS-FUNDING-AND-GTM.md           #   AWS co-sell, ISV Accelerate, funding paths
│
├── infra/
│   ├── cloudformation/                  # 8 nested stacks (cfn-lint clean) + per-agent params
│   └── terraform/                       # 6 modules at parity + per-agent tfvars
│
├── aws-native-reference/                # Per-agent Step Functions ASL (waitForTaskToken HITL)
│
├── decks/                               # 10 AWS-style PowerPoint decks (8 per-agent + executive + CIO)
├── gtm/                                 # Seller cheatsheet, demo storyboard, deck spec, ROI calculator
├── offerings/                           # POC, pilot, assessment, managed service, SOW, battlecard, TCO, TPRM (11 docs)
├── runbooks/                            # Incident response, DR, HITL queue ops, model degradation (4 playbooks)
│
└── scripts/                             # deploy.sh, build_lambdas.sh, run_tests.sh
```

---

## Complete Document Index

### Architecture & Design
- [`docs/SUITE-ARCHITECTURE.md`](docs/SUITE-ARCHITECTURE.md) — six-layer reference architecture, request path, AWS services
- [`ENTERPRISE-PLATFORM.md`](ENTERPRISE-PLATFORM.md) — governed access layer, deny-by-default, HITL, PHI masking, orchestration (ADR-001)
- [`docs/WHY-THE-MCP-LAYER.md`](docs/WHY-THE-MCP-LAYER.md) — rationale for MCP gateway over direct LLM calls

### Deployment & Operations
- [`GETTING-STARTED.md`](GETTING-STARTED.md) — 3 steps: demo on laptop, run test suite, deploy to AWS
- [`docs/DEPLOY-QUICKSTART.md`](docs/DEPLOY-QUICKSTART.md) — empty account → running governed agent
- [`infra/cloudformation/README.md`](infra/cloudformation/README.md) — CloudFormation templates, nesting strategy, per-agent params
- [`infra/terraform/README.md`](infra/terraform/README.md) — Terraform modules, per-agent tfvars
- [`aws-native-reference/README.md`](aws-native-reference/README.md) — Step Functions ASL rebuilds, container vs. native
- [`runbooks/README.md`](runbooks/README.md) — operational playbooks (incident, DR, HITL queue, model degradation)

### Compliance & Security
- [`docs/COMPLIANCE-CONTROL-MAPPINGS.md`](docs/COMPLIANCE-CONTROL-MAPPINGS.md) — regime (HIPAA, CMS, etc.) → control → AWS service
- [`docs/SHARED-RESPONSIBILITY-MATRIX.md`](docs/SHARED-RESPONSIBILITY-MATRIX.md) — AWS / SI / Customer divide
- [`docs/WELL-ARCHITECTED-REVIEW.md`](docs/WELL-ARCHITECTED-REVIEW.md) — AWS WAF review (all five pillars)
- [`docs/STAKEHOLDER-SECURITY-BRIEFINGS.md`](docs/STAKEHOLDER-SECURITY-BRIEFINGS.md) — CISO, CMIO, and compliance officer briefings
- [`governance/README.md`](governance/README.md) — grounding, prompt registry, evals, red team, fairness, accessibility

### Go-to-Market & Sales
- [`SOLUTION-FIELD-GUIDE.md`](SOLUTION-FIELD-GUIDE.md) — per-buyer pitches, qualification questions, land-and-expand
- [`gtm/SELLER-FIRST-MEETING-CHEATSHEET.md`](gtm/SELLER-FIRST-MEETING-CHEATSHEET.md) — 30-second pitch, proof points, qualifying questions
- [`gtm/DEMO-STORYBOARD.md`](gtm/DEMO-STORYBOARD.md) — run-of-show for customer demos
- [`gtm/DECK-CONTENT-SPEC.md`](gtm/DECK-CONTENT-SPEC.md) — deck content specification and slide structure
- [`docs/AWS-FUNDING-AND-GTM.md`](docs/AWS-FUNDING-AND-GTM.md) — AWS co-sell, ISV Accelerate, funding paths
- [`decks/README.md`](decks/README.md) — 10 AWS-style PowerPoint decks (8 per-agent + executive + CIO adoption)
- [`gtm/roi-calculator/`](gtm/roi-calculator/) — ROI calculator workbook and build script

### Consulting Offerings (11 documents)
- [`offerings/POC-OFFERING.md`](offerings/POC-OFFERING.md) — proof-of-concept engagement structure
- [`offerings/PILOT-OFFERING.md`](offerings/PILOT-OFFERING.md) — pilot engagement structure
- [`offerings/ASSESSMENT-OFFERING.md`](offerings/ASSESSMENT-OFFERING.md) — readiness assessment
- [`offerings/MANAGED-SERVICE-OFFERING.md`](offerings/MANAGED-SERVICE-OFFERING.md) — managed service model
- [`offerings/SOW-TEMPLATE.md`](offerings/SOW-TEMPLATE.md) — statement of work template
- [`offerings/BATTLECARD.md`](offerings/BATTLECARD.md) — competitive battlecard
- [`offerings/COMPETITIVE-POSITIONING.md`](offerings/COMPETITIVE-POSITIONING.md) — market positioning
- [`offerings/OBJECTION-HANDLING.md`](offerings/OBJECTION-HANDLING.md) — common objections and responses
- [`offerings/COST-ROI-MODEL.md`](offerings/COST-ROI-MODEL.md) — cost and ROI model
- [`offerings/TCO-MODEL.md`](offerings/TCO-MODEL.md) — total cost of ownership
- [`offerings/TPRM-DUE-DILIGENCE-PACKET.md`](offerings/TPRM-DUE-DILIGENCE-PACKET.md) — third-party risk management

### Contributing & Status
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — conventions: agent isolation, no direct SDK calls, prompt pinning
- [`SUITE-STATUS.md`](SUITE-STATUS.md) — feature matrix, test count, changelog
- [`Makefile`](Makefile) — `make install`, `make test`, `make demo`, `make evals`, `make lint-cfn`, `make decks`, `make roi`

---

## Makefile Targets

```bash
make install      # Install platform_core (editable) + agent deps
make test         # Run the full test suite (121 tests, no API key)
make demo         # Run a deterministic agent demo (AGENT=01-revenue-cycle-denial)
make evals        # Run the governance structural eval harness
make lint-cfn     # cfn-lint all CloudFormation templates
make decks        # Regenerate GTM decks (requires pptxgenjs)
make roi          # Regenerate ROI calculator workbook
make clean        # Remove __pycache__ and .pytest_cache
```

---

## Compliance Disclaimer

This suite is a **decision-support accelerator** for qualified healthcare professionals. It
is not a validated computer system, a certified medical device, or an approved coverage or
billing system. AI-generated content requires human review and approval by a qualified
professional before any consequential action — submitting a claim or appeal, issuing a
coverage determination, signing a clinical note, or closing a case. The AI never takes
irreversible actions autonomously.

Customers are responsible for: computer-system validation (CSV/CSA) for the intended use;
an AWS Business Associate Agreement; IdP integration and role mapping; connector validation
against live systems; Bedrock Guardrail configuration appropriate to their population; and
change-control procedures for prompt and model updates.

This accelerator provides the control design. The customer operationalizes, validates, and
accepts accountability for it.
