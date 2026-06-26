#!/usr/bin/env bash
# Run the full HPP test suite. Each agent is an independent deployable with its own
# top-level `agent`/`tools` packages, so agents are tested in SEPARATE pytest
# invocations (as they are deployed) to avoid module-name collisions. No API key needed.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
FAIL=0
run() { echo "=== $1 ==="; PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$2" python -m pytest $3 -p no:cacheprovider -q || FAIL=1; }

run "platform + governance" "platform_core:." "platform_core/tests governance"
for a in 01-revenue-cycle-denial-agent 02-prior-authorization-agent 03-clinical-administration-agent 04-patient-access-agent; do
  [ -d "$a/tests" ] && run "$a" "platform_core:$a:." "$a/tests"
done
echo; [ "$FAIL" = 0 ] && echo "ALL SUITES PASSED" || echo "SOME SUITES FAILED"
exit $FAIL
