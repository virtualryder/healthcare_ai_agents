# HPP AI Agent Suite — Competitive Positioning

> How the suite is positioned against the four alternatives a healthcare buyer evaluates:
> point solutions, EHR-vendor native AI, build-it-yourself, and other systems integrators.
> The through-line is the platform thesis. Statistics are source-class tagged and traced to
> `../gtm/HPP-DECK-SOURCES.md`.

## The thesis: the governed platform is the asset; agents are interchangeable workloads

A systems integrator deploying AI inside a health system or health plan cannot hand a customer
a collection of LLM calls and call it done. Every artifact an agent touches — a claim, a
clinical note, a prior-auth packet, a coverage recommendation, a member communication — carries
PHI-handling, minimum-necessary, accountability, and (for coverage decisions) "a human decides"
obligations that exist *before* the first line of agent code. The asset that makes any agent
deployable in that environment is the governed control plane: one MCP authorization gateway
(deny-by-default + least-privilege intersection), the framework-enforced human gate, short-lived
tool-scoped tokens, the PHI masker, the append-only audit trail, grounding verification, the
hash-pinned prompt registry, the eval harness and red team, the fairness and accessibility
screens, and the regime→control→AWS mappings. Built once, tested (121 automated tests, no API
key), and reused across all eight agents — so the marginal compliance cost of each new agent
falls. The agents ride on top and are interchangeable; the platform is what you are buying.

## vs. point solutions

A single-workflow tool — a denials bot, a prior-auth assistant — solves one problem and brings
its own governance, or none. Each new vendor is a new BAA, a new audit surface, a new
integration, and a new set of controls to validate. This suite carries one governed control
plane across denials, prior auth, UM, payment integrity, care management, patient access, and
member services. Compliance is consistent across the portfolio, and the second agent reuses the
control plane the first one paid for. Point tools optimize one workflow; the platform optimizes
the cost and defensibility of every workflow you add.

| | Point solution | HPP suite |
|---|---|---|
| Governance | Per-tool, inconsistent | One shared, code-enforced control plane |
| Adding a workflow | New vendor, new BAA, new audit | New workload on the same platform |
| Authorization | Vendor-internal, opaque | Inspectable gateway, deny-by-default, withheld authorities |
| Marginal compliance cost | Resets each time | Falls with each agent |

## vs. EHR-vendor native AI add-ons

EHR-native AI lives on one vendor's surface. It rarely spans payer-side UM/claims, it ties your
AI roadmap to that vendor's release cadence, and it generally does not give you a portable,
inspectable authorization gateway operating under your own AWS BAA. This suite's gateway
semantics are replicated in `platform_core/` — readable and testable without an AWS account —
and run across your systems (Epic / Oracle Health / clearinghouses / payer systems), not just
one EHR. For payers facing CMS-0057-F's 2027 FHIR-API mandate `[gov]`, a FHIR-native,
cross-system approach on AWS HealthLake is structurally better aligned than an EHR add-on. You
keep the control plane and avoid concentrating your AI dependence in a single vendor.

## vs. build-it-yourself

Anyone can wire an LLM call. The expensive, slow, easy-to-get-wrong part is the governance
scaffolding — deny-by-default authorization, the framework-enforced human gate (provably not
bypassable), PHI masking at every boundary, the tamper-evident append-only audit, grounding,
prompt version pinning, the fairness and accessibility screens, and the regulatory mappings.
Building that to a defensible standard once is hard; re-deriving it per workflow is where
in-house programs stall and where shadow AI touching PHI creeps in. This accelerator delivers
that scaffolding built and tested, with an honest maturity ladder (Documented → Demonstrated →
Deployable → Production-ready) so the customer knows exactly what they are inheriting and what
the engagement still has to do.

## vs. other systems integrators

Other SIs can stand up an agent. The differentiators here are specific and demonstrable: a
governed control plane that is enforced **in code, outside the model** (not a slide); withheld
consequential authorities mapped to real roles (`BILLER`, `UM_MEDICAL_DIRECTOR`, signing
clinician); a framework-enforced human gate demonstrable live (LangGraph `interrupt_before`
/ Step Functions `waitForTaskToken`); in-account Bedrock under the customer's BAA with no PHI
egress; eight pre-built workflows on one platform; CloudFormation (cfn-lint clean) and Terraform
parity for per-agent isolated infrastructure; and 121 automated tests that run with no API key.
And we are honest about maturity — production-readiness (CSV/CSA, live connectors, pen test,
HITRUST) is the engagement, not a day-one claim. That honesty is itself a differentiator in a
market full of "production-ready AI" claims.

## The land-and-expand consequence

Because the platform is the asset, the commercial motion compounds. Land with Agent 01
(revenue cycle — the cleanest, most measurable provider ROI), expand to 02 (prior auth) and 04
(patient access) to close the front-to-back-office loop, then to payer-side 05 (UM) and 08
(member services). Every new agent inherits the governed platform; each one is cheaper to make
compliant than the last. Competitors selling point tools or one-off builds cannot match that
declining marginal cost — it is a property of the platform, not the agent.
