# HPP Deck & Positioning — Source of Truth

Every external statistic used in the suite README, agent READMEs, decks, and ROI model is
listed here with a **source class** and URL. Classes: `[gov]` (government/regulatory),
`[peer-reviewed]`, `[industry-research]` (analyst/vendor survey or report),
`[association]` (professional body), `[sector-press]`, `[modeled]` (our calculation).
Verified June 2026.

## Denials & cost-to-collect
- Initial denial rate ~11.8% (2024), climbing into 2025; 41% of providers report >10%
  denial rates. `[industry-research]` — Experian Health, State of Claims 2025.
  https://www.experian.com/blogs/healthcare/state-of-claims-2025/
- U.S. hospitals spent ~$18B in 2025 overturning denials, of ~$43B on billing &
  collections. `[industry-research]` — aggregated vendor/industry reporting 2025.
  https://www.aptarro.com/insights/us-healthcare-denial-rates-reimbursement-statistics
- Administrative cost to rework a denied claim rose $43.84 (2022) → $57.23 (2023); rework
  $25–$181 by complexity. `[industry-research]`
  https://www.aptarro.com/insights/us-healthcare-denial-rates-reimbursement-statistics
- 35–60% of denied claims are never resubmitted. `[industry-research]`
  https://azebratech.com/blog/healthcare-claim-denial-automation/
- Denial rates by payer type — MA ~15.7%, commercial ~13.9%, Medicaid 16.7%, Medicare
  8.4% (initial). `[industry-research]`
  https://www.techtarget.com/revcyclemanagement/feature/Breaking-down-claim-denial-rates-by-healthcare-payer

## Agentic AI adoption (Deloitte, survey of 100 execs — 50 systems, 50 plans, Sep 2025)
- >80% of health-system execs prioritizing agentic AI for clinical operations, care
  delivery, and revenue-cycle management. `[industry-research]`
  https://www.deloitte.com/us/en/industries/life-sciences-health-care/blogs/health-care/ais-next-phase-in-health-care-scale-governance-roi.html
- 70% of health plans prioritizing agentic AI for utilization management, prior
  authorization, and claims. `[industry-research]` — Deloitte, same survey.
- 93% of health-plan execs expect AI to ease prior authorization. `[industry-research]`
  https://www.beckerspayer.com/research-analysis/93-of-health-plan-executives-expect-ai-to-ease-prior-authorization-deloitte/

## Prior-authorization burden (AMA 2024 PA physician survey; Dec 2024; n=1000)
- ~39 PAs per physician per week, ≈13 hours; 40% have staff working exclusively on PA.
  `[association]` https://www.ama-assn.org/practice-management/prior-authorization/fixing-prior-auth-nearly-40-prior-authorizations-week-way
- 94% say PA delays access to necessary care; 78% report it leads to treatment
  abandonment; 89% say it contributes to burnout. `[association]`
  https://www.ama-assn.org/press-center/ama-press-releases/ama-survey-indicates-prior-authorization-wreaks-havoc-patient-care

## Regulatory
- CMS-0057-F Interoperability & Prior Authorization Final Rule — four FHIR APIs (Patient
  Access, Provider Access, Payer-to-Payer, Prior Authorization) by Jan 1, 2027;
  operational provisions + PA denial-reason/turnaround + metrics by Jan 1, 2026. `[gov]`
  https://www.cms.gov/newsroom/fact-sheets/cms-interoperability-prior-authorization-final-rule-cms-0057-f
- No Surprises Act — Good Faith Estimate / balance-billing protections. `[gov]`
  https://www.cms.gov/nosurprises
- HHS Section 1557 nondiscrimination rule (45 CFR Part 92). `[gov]`
  https://www.hhs.gov/civil-rights/for-individuals/section-1557/index.html

## ROI model inputs
- All ROI worksheet inputs are `[modeled]` from the figures above; see
  `../01-revenue-cycle-denial-agent/docs/roi-analysis.md` and `roi-calculator/`.
