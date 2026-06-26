# Model & Prompt Degradation Response — HPP AI Agent Suite

This runbook covers detecting and responding to model or prompt drift — the slow erosion
of grounding, accuracy, or fairness that can creep in when a model version changes, a
prompt is edited, or upstream data shifts. The governance suite is built to catch this
before it reaches a member or a clinical pathway; this runbook is how you operate it.

Posture note: the controls below implement a model-risk-management discipline aligned to
**SR 11-7** (model validation, change control, ongoing monitoring) and the **NIST AI RMF**
(Govern / Map / Measure / Manage). The suite is Demonstrated and Deployable-by-design;
formal CSV/CSA validation is engagement work.

## What can drift

- **Prompt drift** — an edited prompt subtly changes behavior. Prevented by the
  hash-pinned prompt registry: every prompt is content-hashed and pinned, and CI **fails
  on un-bumped drift** (a changed prompt with an unchanged pin is a hard build failure).
- **Model-version drift** — a new Bedrock/foundation-model version changes outputs even
  with an identical prompt. Handled by model-version change control.
- **Grounding decay** — generations cite or assert content not supported by retrieved
  evidence. Caught by grounding verification.
- **Fairness drift** — outcomes diverge across protected groups. Caught by the four-fifths
  (80%) fairness screen on flag/rank/risk-stratify steps (agents 05, 06, 07).

## Detection signals

| Signal | Source | Threshold (tune per engagement) |
|---|---|---|
| Grounding-failure rate | grounding verification metric | Alert when above rolling baseline (e.g., >2x 7-day mean) |
| Eval-harness regression | eval harness in CI / scheduled run | Any drop below the committed pass bar |
| Fairness-screen alert | four-fifths fairness screen | Selection-rate ratio < 0.80 across groups |
| Prompt-hash mismatch | prompt registry CI gate | Any un-bumped change (hard fail) |
| Rising HITL rejection rate | HITL queue metrics | Sustained rise in reviewer rejections |

A rising reviewer-rejection rate (from HITL-QUEUE-OPERATIONS.md) is often the earliest
human signal that the model is producing weaker work product — treat it as a drift lead.

## Response procedure

1. **Triage and classify** the drift (prompt / model-version / grounding / fairness) from
   the signal that fired. Open an incident if member-facing or clinical output is affected
   (cross-ref INCIDENT-RESPONSE.md: grounding-failure spike).
2. **Contain.** The fastest safe action is almost always **rollback to the last
   known-good pinned prompt version** from the registry — it is deterministic and
   instantly revertible because every version is hash-pinned. For a model-version issue,
   pin back to the prior validated model version. Containment must not relax any gate.
3. **Reproduce** under the eval harness. Run the regression suite against the suspect
   prompt/model and confirm the failure is real and bounded.
4. **Diagnose root cause** — prompt edit, model version, retrieval/grounding source
   change, or data shift. Use the append-only audit to pull representative failing
   correlation IDs (PHI-masked) and the grounding results attached to each.
5. **Remediate under change control:**
   - **Prompt fix:** edit the prompt, **bump the pin** (re-hash), and let CI re-baseline —
     an un-bumped change cannot merge.
   - **Model-version change:** treat a new model version as a controlled change — run the
     full eval harness, the red-team suite (injection / PHI-exfil / authz-bypass), and the
     fairness screen before promoting; pin the approved version; record the validation
     evidence.
   - **Grounding source fix:** correct/refresh the retrieval corpus; re-verify.
6. **Validate** before un-rollback: eval harness back above the pass bar, grounding rate
   back to baseline, fairness ratio ≥ 0.80, red-team clean. Capture the evidence package.
7. **Document** in the change record: what drifted, the signal, the root cause, the fix,
   the new pin/version, and the validation results. File the regression as a permanent eval
   case so the same drift fails CI next time.

## Change-control summary (who approves what)

| Change | Gate | Evidence required |
|---|---|---|
| Prompt edit | Prompt-registry pin bump + CI green | Hash bump, eval-harness pass, grounding re-check |
| Model-version promotion | Model change-control review | Eval harness, red team, fairness screen, pinned version |
| Guardrail config change | Security change control | Re-test PII filters + denied topics; no gate weakened |
| Rollback (emergency) | IC authorization | Revert to known-good pin; post-hoc validation |

## Hard rules during any degradation

- Rolling back a prompt or model **never** widens an agent grant or removes a human gate.
- `payer.issue_determination` stays withheld from all agents regardless of model behavior.
- A model that improves on accuracy but fails the fairness screen does **not** ship.
