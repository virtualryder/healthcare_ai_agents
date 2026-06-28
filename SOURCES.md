# Sources — HPP AI Agent Suite

Consolidated, evidence-tiered source list for every external claim in this repository. Tiers:
**[GOV]** government/regulatory · **[PEER-REVIEWED]** · **[INDUSTRY-RESEARCH]** analyst/vendor
survey · **[ASSOCIATION]** professional body · **[SECTOR-PRESS]** · **[VENDOR-REPORTED]** ·
**[MODELED]** our calculation. Per-agent deck figures and URLs are in `gtm/HPP-DECK-SOURCES.md`;
this file adds the regulatory and AWS references.

## Regulatory & compliance
- **HIPAA Privacy/Security Rules** (45 CFR 164) — minimum necessary, audit controls, Safe Harbor de-identification. [GOV]
- **HITECH Act** — breach notification, enforcement. [GOV]
- **42 CFR Part 2** — confidentiality of SUD records; consent to disclose. [GOV]
- **CMS Interoperability & Prior Authorization Final Rule (CMS-0057-F)** — four FHIR APIs by Jan 1, 2027; PA denial-reason + turnaround + metrics. [GOV] https://www.cms.gov/newsroom/fact-sheets/cms-interoperability-prior-authorization-final-rule-cms-0057-f
- **No Surprises Act** — Good Faith Estimate; balance-billing protections. [GOV] https://www.cms.gov/nosurprises
- **ACA Section 1557** (45 CFR Part 92) — nondiscrimination, language access, accessibility. [GOV]
- **21st Century Cures Act** — information-blocking; timely EHI access. [GOV]
- **CMS guidance on AI in utilization management / MA coverage** — a human must make the determination. [GOV]
- **U.S. Senate PSI (2024)** — Medicare Advantage AI-denial findings (post-acute denial rate rise). [GOV]
- **CMS FY2025 Improper Payments** — Medicare FFS $28.83B (6.55%); Medicaid $37.39B (6.12%). [GOV] https://www.cms.gov/newsroom/fact-sheets/fiscal-year-2025-improper-payments-fact-sheet
- **NIST AI RMF 1.0** · **NIST SP 800-53 Rev 5** · **OWASP LLM Top 10 (2025)** · **MITRE ATLAS** — see `docs/`.

## AWS architecture references
- **Amazon Bedrock** (HIPAA-eligible under AWS BAA) + **Guardrails**; in-account inference via VPC endpoint.
- **Amazon Bedrock AgentCore** — Gateway, Identity, Runtime (managed equivalents of the reference gateway).
- **Amazon HealthLake** (FHIR) · **Amazon Comprehend Medical** · **Amazon Bedrock Data Automation**.
- **Amazon Connect** (contact center) · **AWS Step Functions** (`waitForTaskToken` HITL).
- **DynamoDB** (PITR, deny Update/Delete) · **S3 Object Lock** (COMPLIANCE/WORM) · **KMS** · **Cognito** ·
  **CloudTrail / GuardDuty / Security Hub / Config** · **CloudFront + WAF + Shield**.

## Market & outcome statistics
The full set (denials, prior-auth burden, ambient-AI evidence, no-show economics, improper
payments, call-center economics, risk-model fairness, Deloitte adoption) with named sources, dates,
and URLs is in **`gtm/HPP-DECK-SOURCES.md`** — kept in one place so every deck and doc cites the
same numbers.
