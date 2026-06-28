# How HCOS adapts (and extends) the governed-agent pattern for healthcare

The HPP / Health-Providers-&-Plans (HCOS) suite inherits the proven governed-agent architecture
from the SLG and HCLS reference suites and re-grounds it for providers and health plans. The
spine is industry-agnostic; what changed is everything regulated.

## Carried over (the reusable accelerator)
The whole control-plane pattern: the deny-by-default MCP authorization gateway (least-privilege
intersection), the framework-enforced human gate, short-lived scoped tokens, the append-only
audit, the connector framework (fixture/live), the LLM factory (Anthropic / in-account Bedrock +
Guardrails), and the governance spine (grounding, prompt registry, evals, red team, fairness,
accessibility). The per-agent scaffold and the GTM machinery (cited decks + ROI) are reused too.

## Net-new for healthcare (different from government)
- **Buyer & regs:** health-system CFO/CMIO and payer UM/claims VPs; **HIPAA + 42 CFR Part 2 +
  CMS-0057-F + No Surprises Act + Section 1557 + 21st Century Cures**, not CJIS/IRS-1075/StateRAMP.
- **PHI everywhere:** the masker targets HIPAA **Safe Harbor** identifiers (and preserves NPI/ICD/
  CPT as non-PHI reference data); inference stays in-account on **HIPAA-eligible Bedrock under a BAA**.
- **AWS blocks:** **HealthLake** (FHIR), **Comprehend Medical**, **Amazon Connect**, **Bedrock Data
  Automation**, and deterministic medical/benefit rules (e.g., the No Surprises Act Good Faith Estimate).
- **Connectors:** EHR (Epic/Oracle Health via FHIR), clearinghouses/payers (X12 837/835/277/278/270/271),
  encoder (NCCI/MUE), clinical criteria (MCG/InterQual).
- **Withheld authorities tuned to clinical/coverage stakes:** submit-claim (a biller), **issue UM
  determination** (a medical director — withheld from *every* agent), sign a clinical note (a clinician),
  recoup a payment (a human reviewer). An adverse UM recommendation is **forwarded, never auto-denied** —
  the control that makes AI-in-UM defensible under CMS scrutiny.
- **Healthcare-specific governance:** a four-fifths **fairness screen** on UM and risk-stratification
  (the algorithmic-bias concern); a **42 CFR Part 2 consent gate**; a **health-literacy / Section 1557**
  check on member-facing text.

## Where HCOS goes deeper than the inherited pattern
- **Hardened control plane:** cryptographic JWT verification, **bound single-use separation-of-duties
  approvals**, and a **hash-chained** audit — with negative-case tests a CISO can read.
- **Full security package:** SECURITY.md + threat model + NIST 800-53 matrix + OWASP-LLM/ATLAS mapping +
  IR/key-management + production-readiness RACI.
- **Care & Claims Orchestration Platform:** governed saga with compensation + consent ledger + compliance
  event bus tying agents across a patient/member journey — without widening authority.
