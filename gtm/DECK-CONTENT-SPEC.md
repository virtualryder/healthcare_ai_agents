# HPP Deck Content Spec (auditable contract)

Every slide's claims map to a source class in `HPP-DECK-SOURCES.md`. The deck generator
(`../decks/build-agent-decks.js`) renders from this contract; changing a figure means changing
the source file and re-tagging here.

## Per-agent deck (6 slides)
1. **Title** — agent name, suite, "Governed AI on AWS · a human decides every consequential action."
2. **The problem / cost of doing nothing** — 2–3 cited stats for the agent's domain `[source-class]`.
3. **The governed pipeline** — the workflow nodes → the named human gate → finalize; the bright line (withheld authority).
4. **AWS architecture & traffic flow** — MCP gateway → connector → system of record; in-account Bedrock + Guardrails; append-only audit; Step Functions `waitForTaskToken`.
5. **Proof & deploy** — demo (no API key), test count, fixtures, CloudFormation/Terraform, container/native.
6. **The bright line** — what the agent never does autonomously (claim submission / determination / signature / recoupment).

## Executive overview (~11 slides)
Thesis ("the agents are not the product") · the 8-agent portfolio (provider→payer arc) · shared
platform (gateway, PHI masker, LLM factory, connectors) · governance spine (grounding, prompt
registry, evals, red team, fairness, accessibility) · maturity ladder (honest) · AWS building
blocks · land-and-expand (lead with denials) · cost of inaction (denials + prior-auth burden) ·
adoption signal (Deloitte) · CMS-0057-F timeline · call to action.

## CISO / CMIO adoption-review deck
Honest-broker verdict · six gateway controls · "why a CISO can say yes" (controls enforced
outside the model) · withheld authorities (AI assists, a human decides) · PHI residency (in-account
Bedrock under BAA) · shared-responsibility matrix · phased path · go/no-go.

## Source-class tags
`[gov]` government/regulatory · `[industry-research]` analyst/vendor survey · `[association]`
professional body · `[sector-press]` · `[modeled]` our calculation. Full list + URLs:
`HPP-DECK-SOURCES.md`.
