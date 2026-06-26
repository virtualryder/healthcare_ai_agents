# HPP AI Agent Suite
### Governed AI Agents for Health Providers & Plans — Built on AWS

> **The agents are not the product. The governed platform that makes them deployable, auditable, and HIPAA-defensible is.**

A systems integrator deploying AI inside a health system or health plan cannot hand a
customer a collection of LLM calls and call it done. Every artifact an agent touches — a
claim, a clinical note, a prior-authorization packet, a coverage recommendation, a member
communication — carries PHI-handling, minimum-necessary, accountability, and (for coverage
decisions) "a human decides" obligations that exist before the first line of agent code is
written. This suite embeds those controls from the first commit: deny-by-default
authorization, PHI masking, grounding verification, prompt version pinning, a human gate
that is framework-enforced (not merely documented), and a tamper-evident audit trail that
supports the HIPAA Security Rule.

The result is a deployable accelerator — not a certified product — that gives an SI
engagement team a credible, compliant starting point across eight high-value
provider-and-payer workflows.

**Repository status (current):** flagship Agent 01 (Revenue-Cycle & Denial) built to
reference depth with a live Bedrock/connector path · shared `platform_core` + `governance`
built · **107 automated tests passing with no API key** · 7 further agents specified to a
consistent contract and scaffolded · infra, decks, and per-agent builds roll out next.

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

**Agents 01–07 are built to Demonstrated + Deployable-by-design** (full LangGraph
workflow, governed tool access, deterministic fixtures, a flagship test suite, a Streamlit
dashboard, a four-document doc set, and a live Bedrock/connector path each). Agent 01 also
ships **CloudFormation infra** (8 templates, cfn-lint clean). The shared platform and
governance frameworks are built and tested. **Agent 08 is at Documented maturity** with
a per-agent spec README and a scaffold that follows the Agent 01–07 pattern.

---

## The Eight Agents

| # | Agent | Problem it solves | Primary systems | Key regulations |
|---|---|---|---|---|
| **01** | Revenue-Cycle & Denial *(built — flagship)* | Denials reached ~11.8% and climbing; hospitals spent ~$18B in 2025 overturning them and 35–60% of denials are never reworked | Patient accounting, clearinghouse (X12 837/835/277), payer portal, encoder, EHR/FHIR | HIPAA, CMS-0057-F, No Surprises Act, False Claims Act |
| **02** | Prior-Authorization *(built)* | ~39 PAs/physician/week (≈13 hrs); 94% say PA delays care; CMS mandates FHIR PA APIs by 2027 | Payer (Da Vinci CRD/DTR/PAS, X12 278), MCG/InterQual, EHR, IDP | CMS-0057-F, HIPAA, state PA-transparency laws |
| **03** | Clinical-Administration *(built)* | Documentation and inbox burden drive clinician burnout; summaries and drafts compress it | EHR/FHIR (HealthLake, Comprehend Medical), care plan, scheduling, consent | HIPAA, 21st Century Cures, 42 CFR Part 2 |
| **04** | Patient Access *(built)* | Access friction and registration errors drive leakage and downstream denials | Scheduling, registration, payer eligibility (270/271), identity | HIPAA, No Surprises Act, Section 1557 |
| **05** | Utilization Management / Medical Necessity *(built)* | UM is high-volume and under AI scrutiny; the determination must stay human | MCG/InterQual, LCD/NCD, payer, EHR | CMS AI-in-UM guidance, ERISA, NCQA, MH Parity |
| **06** | Payment Integrity & Coding *(built)* | Coding defects drive denials and FCA exposure; integrity recoveries are measurable | Encoder (NCCI/MUE, DRG), patient accounting, clearinghouse, EHR | HIPAA, CMS NCCI, False Claims Act, OIG |
| **07** | Care Management & Population Health *(built)* | Value-based programs depend on care-gap closure and accurate risk capture | Care management, EHR/FHIR, SDOH, consent | HIPAA, CMS risk-adjustment integrity, NCQA, Section 1557, 42 CFR Part 2 |
| **08** | Contact Center / Member Services | Member-service volume spikes around denials and benefits; grounded answers deflect it | Amazon Connect, payer (276/277, 270/271), KB | HIPAA, Section 1557, TCPA |

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

### Governance & Evaluation (`governance/`)

| Control | Implementation |
|---|---|
| **Grounding verification** | Every code/amount/date/policy in an appeal or summary must trace to the source corpus; fails fast rather than hallucinating |
| **Prompt version registry** | Prompts hash-pinned in `governance/prompt_manifest.json`; CI fails on un-bumped drift |
| **Structural eval harness** | Golden-artifact regression (appeal packet, PA packet) — runs in CI with no API keys |
| **HITL gate tests** | Framework-enforced human approval is tested, not merely documented |
| **Red team** | Prompt injection, PHI exfiltration, authorization bypass |
| **Fairness** | EEOC four-fifths screen for UM / risk-stratification flag-and-rank workflows |
| **Accessibility & health literacy** | Section 1557 / WCAG 2.1 AA + plain-language on member-facing output |
| **Control mappings** | Regime (HIPAA, CMS-0057-F, NSA, 1557, 42 CFR Part 2) → platform control → AWS service |

---

## AWS Opportunity

Amazon **HealthLake** (FHIR store for EHR connectors) · Amazon **Connect** (patient access
and member services) · Amazon **Bedrock + AgentCore** (in-account inference, gateway,
identity, runtime) · **Bedrock Data Automation** (clinical-document extraction) · **Step
Functions** (approval orchestration with `waitForTaskToken` human gates) · deterministic
medical/benefit rules engines · **HIPAA controls and human clinical oversight** throughout.

---

## Running the Demo (No API Key Required)

```bash
cd 01-revenue-cycle-denial-agent
pip install -e ../platform_core
pip install langgraph streamlit
export EXTRACT_MODE=demo
python demo/demo_run.py            # three denial paths: appeal / resubmit / escalate
streamlit run app.py               # dashboard at http://localhost:8501

# Full test suite, no API key (each agent is an independent deployable, so its
# own top-level packages are tested in a separate pytest invocation):
cd ..
bash scripts/run_tests.sh
```

---

## Repository Structure

```
healthcare_ai_agents/
├── README.md · SUITE-STATUS.md · ENTERPRISE-PLATFORM.md · SOLUTION-FIELD-GUIDE.md
├── 01-revenue-cycle-denial-agent/      # FLAGSHIP — built to reference depth (+ live path)
├── 02-prior-authorization-agent/       # BUILT — full depth (Demonstrated + Deployable)
├── 03-clinical-administration-agent/     # BUILT — full depth (Demonstrated + Deployable)
├── 04-patient-access-agent/             # BUILT — full depth (Demonstrated + Deployable)
├── 05-utilization-management-agent/     # BUILT — full depth (Demonstrated + Deployable)
├── 06-payment-integrity-coding-agent/   # BUILT — full depth (Demonstrated + Deployable)
├── 07-care-management-pophealth-agent/  # BUILT — full depth (Demonstrated + Deployable)
├── 08-contact-center-member-services-agent/
├── platform_core/hpp_agent_platform/   # LLM factory · PHI masker · MCP gateway · connectors · A2A
├── governance/                          # grounding · prompt registry · evals · red team · fairness · accessibility · controls
├── gtm/                                 # HPP-DECK-SOURCES.md (cited spine) · roi-calculator (roadmap)
├── docs/                                # suite architecture, deployment, GTM (roadmap)
├── infra/cloudformation/               # CloudFormation quick-deploy for Agent 01 (built; cfn-lint clean)
├── infra/terraform/                    # Terraform parity (roadmap)
├── scripts/                            # deploy.sh / build_lambdas.sh (built)
├── aws-native-reference/                # Strands + Step Functions rebuilds (roadmap)
└── offerings/                           # POC / pilot / SOW / battlecard (roadmap)
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
