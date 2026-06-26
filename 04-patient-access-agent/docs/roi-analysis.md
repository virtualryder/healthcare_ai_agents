# Agent 04 — ROI Analysis: Patient Access

> Decision-support accelerator. SA-fillable model; external stats are source-class-tagged in
> `../../gtm/HPP-DECK-SOURCES.md`.

## Why patient access pays back twice
Patient access sits upstream of revenue cycle: eligibility and registration errors are a top
cause of the very denials Agent 01 reworks (e.g. CO-27 terminated coverage). Fixing them at
the front door is cheaper than appealing them at the back. The agent also reduces no-shows
(clearer cost + easier booking) and supports No Surprises Act Good Faith Estimates.

| Driver | Note | Source class |
|---|---|---|
| Front-end avoidable denials | Eligibility/registration defects drive a large share of initial denials | industry-research |
| No Surprises Act GFE | Required for self-pay/uninsured; deterministic estimate tool | gov |
| Access friction → leakage/no-shows | Faster scheduling + transparent cost reduce both | sector-press |

## Value model (fill per customer)
```
Monthly access interactions               A
Minutes of staff time per interaction     m   (e.g. 8)
Agent deflection of routine handling      e   (e.g. 0.5)
Front-end denial rate                     f   (e.g. 0.03)
Avoided-denial net value per claim        R
Loaded staff cost per hour                c

Staff hours returned/month ≈ A * m/60 * e
Front-end denials avoided   ≈ A * f * (improvement)
```
Value shows up as recovered staff capacity, fewer front-end denials (compounding with Agent
01), and reduced no-shows — measured in a pilot.

## What is NOT claimed
The agent does not make coverage determinations or quote a guaranteed price (estimates are
GFE), and it does not book or register without an access-rep approval.
