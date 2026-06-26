# Agent 01 — ROI Analysis: Revenue-Cycle & Denial Management

> A decision-support accelerator. The figures below are an SA-fillable model, not a
> guarantee; every external statistic is source-class-tagged in `../../gtm/HPP-DECK-SOURCES.md`.

## Why denials are the cleanest CFO wedge

| Metric | Value | Source class |
|---|---|---|
| Initial claim denial rate (2024, climbing into 2025) | ~11.8% | industry-research |
| Providers reporting >10% denial rates (2025) | 41% | industry-research |
| U.S. hospital spend overturning denials (2025) | ~$18B | industry-research |
| U.S. hospital spend on billing & collections (2025) | ~$43B | industry-research |
| Administrative cost to rework one denied claim | $25–$181 (≈$57 avg, 2023) | industry-research |
| Denied claims never reworked / resubmitted | 35–60% | industry-research |
| Health-system execs prioritizing agentic AI incl. revenue cycle (Deloitte, Sep 2025) | >80% | industry-research |

The economics: a large share of denied dollars is simply abandoned because rework is
manual and labor-intensive. An agent that triages denials, classifies root cause, and
drafts a grounded, policy-cited appeal in seconds attacks both the **rework unit cost**
and the **never-reworked leakage** at once.

## Value model (fill per customer)

```
Annual claims volume                          C        (e.g. 1,200,000)
Initial denial rate                           d        (e.g. 0.118)
Denied claims                                 D = C*d  (≈ 141,600)
Avg net revenue per denied claim              R        (e.g. $180)
Share currently never reworked                n        (e.g. 0.45)
Recovery lift on newly-worked denials         r        (e.g. 0.55 overturn)
Fully-loaded cost to rework one claim         k        (e.g. $57)
Agent deflection of manual rework effort      e        (e.g. 0.50)

Recovered revenue   ≈ D * n * r * R
Rework cost avoided  ≈ D * (1-n) * k * e
```

Plug-in example (illustrative, not a quote): D≈141,600; recovered ≈ 141,600 × 0.45 ×
0.55 × $180 ≈ **$6.3M/yr** of previously-abandoned revenue, plus rework-cost avoidance on
the worked population. The SA workbook in `../../gtm/roi-calculator/` makes these inputs
editable and outputs a one-page CFO summary.

## What is NOT claimed
The agent does not auto-submit claims or appeals, does not make coverage or payment
determinations, and does not replace a coder or denials specialist. Value comes from
compressing the analyst minutes per denial and from reducing leakage — both measured in
a pilot, not assumed.
