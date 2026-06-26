# Agent 07 — ROI Analysis: Care Management & Population Health

> Decision-support accelerator. SA-fillable model; external stats are source-class-tagged in
> `../../gtm/HPP-DECK-SOURCES.md`.

## Value drivers
| Driver | Note | Source class |
|---|---|---|
| Care-gap closure | Drives quality scores (HEDIS/Stars) and value-based incentives | sector-press |
| Accurate risk capture (HCC/RAF) | Underpins value-based payment; must be defensible | gov |
| Agentic AI for care delivery | >80% of health-system execs prioritizing | industry-research (Deloitte 2025) |
| Fairness in risk models | Section 1557 + CMS risk-adjustment integrity | gov |

The agent compresses the care manager's gap-identification, risk-review, and outreach-drafting
time, and makes the risk-stratification step auditable and fairness-screened. Value is recovered
care-manager capacity, more closed gaps (quality/Stars revenue), and a defensible risk process.

## Value model (fill per customer)
```
Panel size (members)                      M
Care-management touches/member/year       t
Minutes per touch (gap review + outreach) m   (e.g. 15)
Agent deflection of prep/draft work       e   (e.g. 0.45)
Loaded care-manager cost per hour         c

Care-manager hours returned/year ≈ M * t * m/60 * e
Closed-gap quality value           ≈ (incremental gaps closed) * value/gap
```

## What is NOT claimed
The agent does not change a care plan, send outreach, or assign risk autonomously; the care
manager signs off and owns the plan. Sensitive (Part 2) records are gated. Value is measured in
a pilot, not assumed.
