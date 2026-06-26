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

## Per-agent story metrics (added for the per-agent decks — verified June 2026)

### 01 Revenue-Cycle & Denial — market adoption / solving
- 40% of health systems piloting/implementing gen AI in RCM; 39% exploring; ~20% not started.
  Smaller systems ($500M–$1B) ~20% vs >half (64%) of larger systems. 90% of rev-cycle leaders
  expect gen AI to grow in coding. `[industry-research]` — AKASA/HFMA Pulse Survey, 519 CFOs/rev-cycle
  leaders, Apr 2025. https://www.fiercehealthcare.com/ai-and-machine-learning/adoption-ai-hospital-rcm-surges-even-health-systems-navigate-cost
- Autonomous coding at Inova Health: −$500K annual coding cost, −50% weekly DNFB, +10% charge
  capture. `[sector-press]` — AKASA/Inova.

### 02 Prior-Authorization — market solving
- June 2025: 50+ health plans pledged to simplify PA, including real-time approval for ≥80% of
  requests. `[sector-press]` — federal/industry pledge. AI-PA tools have shown ~82% overturn-on-appeal
  in some deployments. https://www.healthcaredive.com/news/medicare-advantage-AI-denials-cvs-humana-unitedhealthcare-senate-report/730383/

### 03 Clinical-Administration — ambient AI evidence
- Ambient AI scribe QI study (263 clinicians, 6 systems): ambulatory burnout 51.9% → 38.8% in 30
  days. UW Health −30 min/day documentation; ~8.5% less total EHR time, >15% less note-composition
  time; +0.49 visits/week. `[peer-reviewed]` — JAMA 2025 / AHA / UChicago Medicine.
  https://www.uchicagomedicine.org/forefront/research-and-discoveries-articles/ambient-ai-saves-time-reduces-burnout-fosters-patient-connection

### 04 Patient Access — no-show economics
- U.S. outpatient no-show rate ~23–33%; avg cost of a missed appointment ~$200; estimated ~$150B/yr
  to the U.S. system. `[industry-research]` — Curogram / Dialog Health / MGMA 2024–2025.
  Amazon Connect Health: conversational identity verification + appointment management.
  https://www.dialoghealth.com/post/patient-no-show-statistics

### 05 Utilization Management — scrutiny / solving
- U.S. Senate PSI (2024): UnitedHealth post-acute denial rate rose 8.7% → 22.7% (2019–2022) after
  NaviHealth. nH Predict alleged ~90% error rate / >80% of denials reversed on appeal (litigation).
  CMS Wasteful & Inappropriate Services Reduction (WISeR) model launched July 2025 across 6 states,
  tracking overturned-denial rates. `[gov]` `[sector-press]` —
  https://www.healthcaredive.com/news/medicare-advantage-AI-denials-cvs-humana-unitedhealthcare-senate-report/730383/

### 06 Payment Integrity & Coding — improper payments
- Medicare FFS improper payments $28.83B (6.55%, FY2025); Medicaid $37.39B (6.12%); 77% of Medicaid
  improper payments are insufficient documentation. MA coding-driven overpayment ~$40B (MedPAC 2025).
  Medicare program-integrity ROI 22.3:1 in FY2025 (savings $26.3B→$41.9B, +59%). `[gov]` — CMS FY2025
  Improper Payments Fact Sheet; MedPAC. https://www.cms.gov/newsroom/fact-sheets/fiscal-year-2025-improper-payments-fact-sheet

### 07 Care Management & Population Health — risk-model fairness
- A widely used commercial risk-stratification algorithm (Optum) showed racial bias: it cut the
  number of Black patients identified for extra care by more than half (it predicted cost, not
  illness); Black patients had 26.3% more chronic conditions at the same risk score; ~200M people
  affected by similar tools. `[peer-reviewed]` — Obermeyer et al., Science 2019.
  https://www.healthcarefinancenews.com/news/study-finds-racial-bias-optum-algorithm

### 08 Contact Center / Member Services — call economics
- Healthcare live-agent call ~$25–$35 per ticket (vs $6–$15 general). AI deflects ~45% of queries.
  Amazon Connect Customer AI: one healthcare group cut contact-center cost ~45%/yr and +12-pt
  satisfaction; Amazon Connect Health adds conversational identity verification + appointment mgmt.
  `[industry-research]` `[sector-press]` — Hyro State of Healthcare Call Centers 2025; D3Clarity; AHA.
