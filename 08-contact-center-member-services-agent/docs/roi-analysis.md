# Agent 08 — ROI Analysis: Contact Center / Member Services

> Decision-support accelerator. SA-fillable model; external stats are source-class-tagged in
> `../../gtm/HPP-DECK-SOURCES.md`.

## Value drivers
Member-services volume concentrates around the same denials and benefits questions the rest of
the suite touches. Grounded, identity-verified self-service and rep assist deflect routine
contacts, shorten handle time, and improve member experience (CAHPS/Stars).

| Driver | Note | Source class |
|---|---|---|
| Contact volume around denials/benefits | Spikes track the CO-197 denials Agent 01 works | sector-press |
| Agentic AI for member operations | Plans prioritizing AI for claims/member ops | industry-research (Deloitte 2025) |
| Member experience (CAHPS/Stars) | Clear, fast answers improve scores and retention | sector-press |

## Value model (fill per customer)
```
Monthly member contacts                   K
Minutes per contact (handle + after-call) m   (e.g. 7)
Agent deflection / assist factor          e   (e.g. 0.4)
Loaded rep cost per hour                   c

Rep hours returned/month ≈ K * m/60 * e
Annualized capacity recovered ≈ (monthly hours) * 12 * c
```
Value is recovered rep capacity, shorter handle time, and improved member experience — with
identity verification and a human gate keeping every disclosure and record defensible.

## What is NOT claimed
The agent does not make coverage decisions, submit appeals, or disclose account data without a
verified identity; logging and grievance filing require rep approval. Value is measured in a
pilot, not assumed.
