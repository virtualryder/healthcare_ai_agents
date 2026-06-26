# Agent 02 — ROI Analysis: Prior-Authorization

> A decision-support accelerator. Figures are an SA-fillable model; external stats are
> source-class-tagged in `../../gtm/HPP-DECK-SOURCES.md`.

## The burden
| Metric | Value | Source class |
|---|---|---|
| Prior authorizations per physician per week | ~39 (≈13 hours) | association (AMA 2024) |
| Practices with staff working exclusively on PA | 40% | association |
| Physicians saying PA delays necessary care | 94% | association |
| Physicians reporting PA-driven treatment abandonment | 78% | association |
| Health plans prioritizing agentic AI for UM/PA/claims | 70% | industry-research (Deloitte 2025) |
| Plan execs expecting AI to ease PA | 93% | industry-research |
| CMS-0057-F FHIR Prior Auth API deadline | Jan 1, 2027 | gov |

## Value model (fill per customer)
```
PA volume per provider/week              V   (e.g. 39)
Providers in scope                       P
Minutes of staff time per PA today       m   (e.g. 20)
Agent deflection of assembly/admin time  e   (e.g. 0.55)
Loaded staff cost per hour               c

Weekly staff hours returned ≈ V * P * m/60 * e
Annualized cost avoided      ≈ (weekly hours) * 52 * c
```
The agent also compresses **authorization cycle time** (controlled vendor pilots have reported
60–70% reductions), which reduces care delays and downstream denials (CO-197) — the same
denials Agent 01 works. CMS-0057-F readiness is a second driver for plan-side buyers.

## What is NOT claimed
The agent does not approve, deny, or determine coverage; it does not submit without a PA-nurse
approval. Value comes from compressing evidence-assembly and submission minutes and from cycle-
time reduction — measured in a pilot, not assumed.
