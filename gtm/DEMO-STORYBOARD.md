# HPP Demo Storyboard — repeatable ~25-minute run of show

A no-API-key, deterministic demo that proves the governance thesis across the provider→payer arc.
Everything below runs with `EXTRACT_MODE=demo`.

## 0. Frame (2 min)
"The agents are not the product — the governed platform that makes them deployable, auditable,
and HIPAA-defensible is. Watch what the agent **never** does on its own."

## 1. Revenue-Cycle & Denial — the wedge (6 min)
```bash
cd 01-revenue-cycle-denial-agent && EXTRACT_MODE=demo python demo/demo_run.py
```
Show three denial paths (appeal / resubmit / escalate). Land: a CO-197 denial is classified, a
**grounded** appeal is drafted with policy citations, and it **pauses at the denials-specialist
gate** — the agent cannot submit a claim. Open `app.py` (Streamlit) and approve to submit the appeal.
Cited stakes: ~$18B/yr overturning denials; 35–60% never reworked `[industry-research]`.

## 2. Prior-Authorization — the payer 2027 driver (4 min)
```bash
cd 02-prior-authorization-agent && EXTRACT_MODE=demo python demo/demo_run.py
```
Imaging requires PA (Da Vinci CRD), criteria are evaluated, a rationale is assembled, and it
pauses at the **PA-nurse gate**; an office visit needs no PA; urgent escalates. Stakes: 39
PAs/physician/week, 94% say PA delays care `[association]`; CMS-0057-F FHIR PA APIs by 2027 `[gov]`.

## 3. Utilization Management — the governance crown jewel (5 min)
```bash
cd 05-utilization-management-agent && EXTRACT_MODE=demo python demo/demo_run.py
```
Show a "does not meet" recommendation — and that it is **forwarded for a human determination,
never auto-denied**. Show the **fairness-flagged** cohort. Land the headline: `issue_determination`
is withheld from **every** agent; even a medical-director session cannot issue a determination
*through* the agent (a passing test asserts it). This is what makes an AI-in-UM deployment defensible.

## 4. The governance spine (4 min)
```bash
PYTHONPATH=platform_core:. python -m pytest governance -q
PYTHONPATH=platform_core:. python -m governance.evals.run_evals
```
Grounding, hash-pinned prompt registry, red team (injection / PHI-exfil / authz-bypass),
four-fifths fairness, accessibility — all run in CI with **no API key**.

## 5. Deploy story (3 min)
Show `infra/cloudformation/` (cfn-lint clean, per-agent isolated VPC/KMS/Cognito/audit/gateway),
`scripts/deploy.sh`, and the `waitForTaskToken` human gate in `aws-native-reference/`. In-account
Bedrock under the AWS BAA — no PHI egress.

## 6. Close (1 min)
"Land with denials (cleanest CFO ROI), expand across the suite. Every new agent inherits the same
governed platform — the marginal compliance cost falls with each one."
