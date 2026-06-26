# HPP AI Agent Suite — Cost & ROI Model (Narrative Framework)

> A decision-support framework, not a guarantee. It ties agent value to the documented
> denial and prior-authorization burden, gives an SI/SA a structure to populate with the
> customer's own numbers, and points to the per-agent value models. Every external statistic
> is source-class tagged and traceable to `../gtm/HPP-DECK-SOURCES.md`. Per-agent value
> models live in each agent's `docs/roi-analysis.md` (e.g.
> `../01-revenue-cycle-denial-agent/docs/roi-analysis.md`).

## The thesis

Value comes from compressing the human minutes spent per transaction and from reducing
leakage — work that is currently abandoned because it is manual. The agent does not auto-submit
claims or appeals, does not make coverage or payment determinations, and does not replace a
specialist. Returns are measured in a pilot, not assumed.

## Agent 01 — Revenue-Cycle & Denial (the lead CFO case)

The denials problem is large and well-documented. Initial denial rates reached ~11.8% in
2024 and are climbing; 41% of providers report denial rates above 10% `[industry-research]`.
U.S. hospitals spent ~$18B in 2025 overturning denials, out of ~$43B on billing and
collections `[industry-research]`. The administrative cost to rework a single denied claim
ran ~$57 on average in 2023 ($25–$181 by complexity) `[industry-research]`, and 35–60% of
denied claims are never reworked at all `[industry-research]`. Two levers follow directly:
the **rework unit cost** the agent compresses, and the **never-reworked leakage** the agent
recovers by making rework cheap enough to attempt.

The fillable value model (see Agent 01's `docs/roi-analysis.md`):

```
Annual claims volume                          C        (e.g. 1,200,000)
Initial denial rate                           d        (e.g. 0.118)
Denied claims                                 D = C*d  (≈ 141,600)
Avg net revenue per denied claim              R        (e.g. $180)
Share currently never reworked                n        (e.g. 0.45)
Recovery lift on newly-worked denials         r        (e.g. 0.55 overturn)
Fully-loaded cost to rework one claim         k        (e.g. $57)
Agent deflection of manual rework effort      e        (e.g. 0.50)

Recovered revenue    ≈ D * n * r * R
Rework cost avoided  ≈ D * (1-n) * k * e
```

Illustrative only, not a quote: with D≈141,600, recovered ≈ 141,600 × 0.45 × 0.55 × $180 ≈
**$6.3M/yr** of previously-abandoned revenue, plus rework-cost avoidance on the worked
population `[modeled]`. All inputs are editable per customer.

## Agent 02 / 05 — Prior-Authorization and Utilization Management (payer and provider)

The prior-authorization burden is the second cleanest case. Physicians complete ~39 prior
authorizations per week, about 13 hours, and 40% have staff working exclusively on PA
`[association]`; 94% say PA delays necessary care, 78% report treatment abandonment, and 89%
say it contributes to burnout `[association]`. On the plan side, 93% of health-plan execs
expect AI to ease prior authorization `[industry-research]`. The value model mirrors Agent 01:
PA volume × minutes-per-PA × deflection for the time lever, plus turnaround-time reduction and
avoided care-delay/abandonment for the quality lever. Agents 02 and 05 prepare requirement
checks, assemble evidence, evaluate criteria (MCG/InterQual, LCD/NCD), and draft grounded
recommendations — but never issue a determination; that authority is withheld from every agent
and held only by a `UM_MEDICAL_DIRECTOR`. See each agent's `docs/roi-analysis.md`.

## Portfolio economics

The largest cost in a HIPAA AI deployment is the governance scaffolding, and it is paid once.
The MCP authorization gateway, PHI masker, human gate, audit trail, prompt registry, eval
harness, fairness and accessibility checks, and the regime→control→AWS mappings are shared
across all eight agents. So the marginal compliance cost of each additional agent falls — the
second agent reuses the control plane the first one paid for. This is the financial expression
of the platform thesis: the governed platform is the asset; the agents are interchangeable
workloads on top of it.

## How to use this with a customer

1. Pull the customer's actuals: claim/PA volume, denial rate, net revenue per claim, current
   rework cost and never-reworked share, FTE counts on denials/PA.
2. Populate the relevant agent's `docs/roi-analysis.md` value model and the SA workbook.
3. Net against run cost from `TCO-MODEL.md` and SI fees from the relevant offering.
4. Present a one-page CFO/CFO-equivalent summary with the threshold to fund a pilot.
5. Measure the realized lift in the pilot; do not promise it in the sale.

## What is not claimed

No outcome is guaranteed. The agent assists, drafts, assembles, flags, and recommends; a
licensed or credentialed human makes every consequential decision. All ROI figures are
`[modeled]` from the cited source statistics and become real only when measured in a pilot.
