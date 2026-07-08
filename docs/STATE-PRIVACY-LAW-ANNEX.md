# State privacy-law annex (US) — HPP AI Agent Suite

**Scope & honesty.** This annex complements [`COMPLIANCE-CONTROL-MAPPINGS.md`](COMPLIANCE-CONTROL-MAPPINGS.md)
(HIPAA/HITECH, 42 CFR Part 2, CMS rules) with the **US state** health-privacy and consumer-privacy
laws that increasingly reach health-plan and provider AI workflows even where HIPAA already applies.
It maps each regime to the platform controls that support compliance. It is **not legal advice and
not a compliance attestation** — it is a reference for the customer's privacy counsel and security
officers, who own the determination for their jurisdictions, data, and configuration. Statutes and
effective dates change; verify current text before relying on this.

## Why state law matters when HIPAA already applies

HIPAA is a floor, not a ceiling. Three gaps pull state law into these workflows:

1. **Non-HIPAA data.** Consumer health data collected outside a HIPAA-covered relationship (apps,
   marketing, web forms feeding a contact-center agent) is often *not* PHI but *is* regulated by
   state consumer-health-data laws.
2. **Stricter state standards.** Several states impose consent, minimization, or private-right-of-
   action requirements stricter than HIPAA for the same data.
3. **AI-specific rules.** A growing set of states regulate automated decision-making and profiling,
   which touches utilization-management and payment-integrity agents.

## Regime map

| Regime | Reaches | Key obligation | Supporting platform control |
|---|---|---|---|
| **WA My Health My Data Act (MHMDA)** (eff. 2024) | Consumer health data beyond HIPAA; broad "regulated entity" definition | Opt-in consent for collection *and* separate consent for sharing; geofencing ban around health facilities; private right of action | PHI/consumer-data masking at every boundary; deny-by-default gateway limits which tools may read/share data; append-only audit evidences consent-gated access |
| **NV SB 370** (consumer health data) | Similar to MHMDA, Nevada consumers | Consent for collection/sharing; no sale without authorization | Same as above; token-scoped connectors bound to purpose |
| **CA CMIA** (Confidentiality of Medical Information Act) | Medical info held by providers, contractors, and certain apps | Authorization before disclosure; specific breach remedies | Human-gate on any disclosure-type action; consequential actions withheld in code; audit trail |
| **CA CCPA/CPRA** | Personal info incl. sensitive PI where the **HIPAA carve-out does not apply** (non-PHI) | Sensitive-PI limits, opt-out of certain sharing, ADM/profiling regulations (rulemaking) | Data-class isolation separates PHI (HIPAA) from consumer PI (CCPA); masker + audit |
| **CO Privacy Act / CT / VA / OR / TX (TDPSA) / others** (comprehensive state privacy) | Health data as "sensitive data" for non-HIPAA processing | Consent for sensitive data; DPIA/assessment for high-risk profiling | Grounding + human-gate reduce automated-decision risk; audit supports the required assessments |
| **State UM / AI-in-coverage rules** (e.g., CA SB 1120) | Utilization-management determinations | A licensed human must make/deny medical-necessity decisions; AI may assist only | **`payer.issue_determination` is withheld from every agent**; UM agent drafts and flags only — the bright line is enforced in code, not policy |
| **State breach-notification laws (50-state)** | Any resident PII/PHI breach | Timely notification; content requirements | Append-only + WORM audit provides the forensic record; incident-response runbook |

## Design consequences already in the suite

- **Determinations stay human.** Coverage, medical-necessity, claim-submission, and recoupment
  actions are withheld from every agent and require a bound, single-use, separation-of-duties human
  approval — this is what satisfies the "a person must decide" thrust of CA SB 1120 and CMIA-style
  disclosure rules.
- **Data-class isolation** lets a deployment treat PHI (HIPAA/BAA path) and non-PHI consumer health
  data (state-law path) under different controls, regions, and retention — rather than forcing one
  regime onto everything.
- **Consent-gated access** is expressible through the gateway's grant∩entitlement model and evidenced
  in the append-only audit, which is what a MHMDA/CMIA reviewer asks to see.

## Customer-owned (not provided by this repo)

- Legal determination of which state regimes apply to the customer's entities and data.
- Consent capture/management UX and the system of record for consent (the agents consume a consent
  signal; they do not originate legally-sufficient consent).
- State-specific DPIAs/assessments and breach-notification execution.
- Data-residency choices where a state or contract requires in-state or in-region processing (reached
  via the customer's chosen AWS Region; Bedrock and Comprehend Medical are regional services reached
  over PrivateLink under the customer's BAA — traffic stays on AWS private networking, no egress to
  external AI APIs).

See also: [`COMPLIANCE-CONTROL-MAPPINGS.md`](COMPLIANCE-CONTROL-MAPPINGS.md),
[`../assurance/README.md`](../assurance/README.md), and the
[`PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md`](PRODUCTION-READINESS-AND-SHARED-RESPONSIBILITY.md)
RACI.
