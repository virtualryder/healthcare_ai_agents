# Governance & Evaluation Framework
Built in from the first commit. All run with **no API key**.

| Control | File | What it enforces |
|---|---|---|
| Grounding verification | `grounding.py` | No fabricated code/amount/date/policy reaches a payer, clinician, or patient |
| Prompt registry | `prompt_registry.py` + `prompt_manifest.json` | Hash-pinned prompts; CI fails on un-bumped drift |
| Eval harness | `evals/run_evals.py` | Golden-artifact structural regression (appeal packet, PA packet) |
| Red team | `redteam/scenarios.py` | Prompt injection, PHI exfiltration, authorization bypass |
| Fairness | `fairness/disparate_impact.py` | EEOC four-fifths rule for UM / risk-strat flag/rank workflows |
| Accessibility & health literacy | `accessibility/wcag.py` | Section 1557 / WCAG 2.1 AA + plain-language on member output |
| Control mappings | `controls/control_mappings.py` | Regime (HIPAA, CMS-0057-F, NSA, 1557, 42 CFR Part 2) -> control -> AWS service |
| HITL enforced | `tests/test_hitl_enforced.py` | High-risk tools cannot execute without approval |

Run: `PYTHONPATH=../platform_core:.. python -m pytest governance -q`
