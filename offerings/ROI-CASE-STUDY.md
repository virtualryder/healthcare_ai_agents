# Worked ROI case study — Revenue-Cycle Denial Drafting (Agent 01)

**What this is.** A fully worked, illustrative ROI example with totals — the value counterpart to
[`TCO-MODEL.md`](TCO-MODEL.md) (which is cost only). It uses a hypothetical mid-size provider and
**illustrative, source-tagged assumptions**; it is not a guarantee and not a customer result. Replace
the bracketed inputs with the customer's actuals. `[MODEL ASSUMPTION]` marks every editable driver.

## Scenario: a 400-bed health system, provider revenue cycle

| Input | Value | Source |
|---|---|---|
| Annual claims | 1,200,000 | `[MODEL ASSUMPTION]` |
| Initial denial rate | 11.8% → 141,600 denials/yr | `[INDUSTRY-RESEARCH]` industry avg ~11.8% |
| Denials worked today (staffing-limited) | 55% → ~77,900 | `[MODEL ASSUMPTION]` |
| Denials **not** worked (written off) | 45% → ~63,700 | derived |
| Avg recoverable value per worked denial | $250 net | `[MODEL ASSUMPTION]` |
| Appeal-drafting time today | ~30 min/denial | `[INDUSTRY-RESEARCH]` |

## The intervention

Agent 01 **drafts** the appeal packet (pulls the denial reason, matches policy, assembles the
evidence) — a human coder reviews and submits. **Claim submission is withheld from the agent**; a
person signs. Two value levers:

1. **Throughput:** drafting time drops from ~30 min to ~8 min of review → the same staff work more
   denials. `[MODEL ASSUMPTION]` conservative 2.5× effective throughput on the drafting step.
2. **Coverage:** more of the 45% currently-written-off denials get worked.

## Worked value (illustrative)

| Line | Calculation | Annual value |
|---|---|---|
| Additional denials worked (coverage 55% → 80%) | (0.80 − 0.55) × 141,600 = 35,400 more | — |
| Recovered revenue on those | 35,400 × $250 | **$8,850,000** |
| Staff time reclaimed on the existing 77,900 | 77,900 × 22 min saved ÷ 60 × $40/hr loaded | **$1,142,000** |
| **Gross annual benefit (illustrative)** | | **~$9.99M** |

## Cost side (from TCO-MODEL.md)

| Line | Annual |
|---|---|
| AWS run cost (production scale, from TCO-MODEL) | ~$30,204/yr |
| Implementation + integration (one-time, engagement) | `[MODEL ASSUMPTION]` $150,000–$400,000 |
| Ongoing human review (already staffed; reallocated) | included above |

## ROI

Even on the **cost-reclaim lever alone** ($1.14M) against ~$30K/yr AWS + a $250K one-time build, the
first-year return is strongly positive; including recovered revenue the payback is a small fraction of
a year. The point for the CIO: **the AWS consumption (~$30K/yr) is a rounding error against the value
of one back-office workflow** — the gate is trust and integration, not cost.

## Honesty rails

- Illustrative model, not a customer outcome or guarantee. Denial rates, recovery values, and staffing
  vary widely — use the customer's actuals.
- The agent **drafts**; humans decide and submit. Value assumes that human-in-the-loop model, not
  autonomous claim submission.
- Bedrock token volume is the dominant variable cost (see TCO-MODEL sensitivity). A 2× volume change
  moves AWS cost by ~$1.5K/mo — immaterial to this ROI.
- Start with a synthetic-data pilot to validate draft quality before quoting a recovery number.
