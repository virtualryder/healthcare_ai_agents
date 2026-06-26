# Agent 03 — ROI Analysis: Clinical-Administration

> Decision-support accelerator. SA-fillable model; external stats are source-class-tagged in
> `../../gtm/HPP-DECK-SOURCES.md`.

## The burden
| Driver | Note | Source class |
|---|---|---|
| Documentation & inbox load | Leading contributor to clinician burnout and after-hours "pajama time" | sector-press |
| Agentic AI priority | >80% of health-system execs prioritizing agentic AI for clinical operations & care delivery | industry-research (Deloitte 2025) |
| Info-blocking (Cures Act) | Timely EHI access required — summaries surface, never withhold | gov |

## Value model (fill per customer)
```
Clinicians in scope                       N
Admin/documentation minutes per day       d   (e.g. 90)
Agent deflection of draft/summary effort  e   (e.g. 0.4)
Loaded clinician cost per hour            c

Daily minutes returned per clinician ≈ d * e
Annualized capacity recovered        ≈ N * (d*e/60) * working_days * c
```
The agent compresses chart-summary, discharge-doc, referral, and inbox-draft time; the value
shows up as recovered clinician capacity and reduced after-hours documentation, plus fewer
downstream errors from incomplete handoffs at care transitions.

## What is NOT claimed
The agent does not enter orders, sign notes, or make clinical decisions; patient-facing and
SUD-sensitive material is gated. Value is measured as recovered minutes and handoff quality in
a pilot, not assumed.
