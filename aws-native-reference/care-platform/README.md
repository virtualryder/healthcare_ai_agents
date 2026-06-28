# AWS-Native — Care & Claims Orchestration Platform

The in-process saga (`care_platform/hpp_care_platform/`) maps to an **Amazon Step Functions**
state machine: each journey step is a Task that calls the agent's tool through the governed
gateway; **compensation** is a `Catch` → compensating-Task path; the **human gate** is a
`waitForTaskToken` Task; and every transition emits a hash-chained compliance event to the
append-only audit. Authority never widens — each step authorizes through the same MCP gateway
with the acting user's claims.

Run the reference locally (no API key):
```bash
PYTHONPATH=platform_core:care_platform python aws-native-reference/care-platform/local_runner.py
```
Journeys: `denial_to_resolution` (01→06→01→08), `admission_to_followup` (05→03→07→04),
`new_member_onboarding` (04→04→07). See `../../ENTERPRISE-PLATFORM.md`.
