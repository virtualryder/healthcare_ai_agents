#!/usr/bin/env python3
"""check_maturity.py — portfolio drift-checker for MATURITY.yaml's test count.

MATURITY.yaml is the single source of truth for this repo's maturity claims,
including `tests.offline_total`. Prose defers to MATURITY.yaml; this tool keeps
the declared count honest by re-collecting the offline suite and comparing.

The offline suite is run exactly as `tests.reproduce` documents: via
scripts/run_tests.sh, which invokes pytest **per suite in isolation**
(each agent ships its own top-level `agent`/`tools` packages, so a single
pytest process over every path would import the wrong agent's modules and
mis-count). This tool mirrors that isolation and sums the collected node ids.

Usage:
    python tools/check_maturity.py            # verify; exit 0 if aligned, 1 on drift
    python tools/check_maturity.py --update   # rewrite offline_total to the collected count

Stdlib-only. No API key. No third-party deps beyond pytest (already required to run the suite).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MATURITY = REPO_ROOT / "MATURITY.yaml"
RUN_TESTS = REPO_ROOT / "scripts" / "run_tests.sh"

# Regex for the top-line declaration in MATURITY.yaml, e.g. "  offline_total: 258   # comment"
_OFFLINE_RE = re.compile(r"^(?P<prefix>\s*offline_total:\s*)(?P<num>\d+)(?P<rest>.*)$", re.MULTILINE)


def read_declared() -> int:
    m = _OFFLINE_RE.search(MATURITY.read_text())
    if not m:
        sys.exit("ERROR: could not find `offline_total:` in MATURITY.yaml")
    return int(m.group("num"))


def derive_suites() -> list[tuple[str, str, list[str]]]:
    """Derive (pythonpath, label, paths) suites from scripts/run_tests.sh.

    `tests.reproduce` points at scripts/run_tests.sh; we parse its `run` calls so the
    collection matches what actually executes. Explicit `run "label" "PP" "paths"` lines
    give the fixed suites; the per-agent loop is expanded by globbing `NN-*-agent/tests`.
    """
    text = RUN_TESTS.read_text()
    suites: list[tuple[str, str, list[str]]] = []
    # Explicit run lines: run "<label>" "<pythonpath>" "<space-separated paths>"
    for m in re.finditer(r'^\s*run\s+"([^"]*)"\s+"([^"]*)"\s+"([^"]*)"', text, re.MULTILINE):
        label, pp, paths = m.group(1), m.group(2), m.group(3)
        if "$a" in pp or "$a" in paths:
            continue  # the loop body — expanded below
        suites.append((pp, label, paths.split()))
    # Per-agent loop: one isolated suite per NN-*-agent that has a tests/ dir.
    for agent_dir in sorted(REPO_ROOT.glob("[0-9][0-9]-*-agent")):
        tests = agent_dir / "tests"
        if tests.is_dir():
            name = agent_dir.name
            suites.append((f"platform_core:{name}:.", name, [f"{name}/tests"]))
    return suites


def _count_collected(output: str) -> int:
    """Count collected tests from `pytest --collect-only -q` output, version-robustly.

    pytest >=8.4/9.x prints one `path/to/test_file.py: N` line per file; older pytest
    prints one `path::node id` line per test. Handle both.
    """
    per_file = re.findall(r"^.+\.py:\s*(\d+)\s*$", output, re.MULTILINE)
    if per_file:
        return sum(int(n) for n in per_file)
    return sum(1 for line in output.splitlines() if "::" in line)


def collect_actual() -> int:
    total = 0
    for pythonpath, label, paths in derive_suites():
        cmd = [
            sys.executable, "-m", "pytest", *paths,
            "-p", "no:cacheprovider", "--import-mode=importlib", "--collect-only", "-q",
        ]
        env = {"PYTHONPATH": pythonpath, "PYTHONDONTWRITEBYTECODE": "1"}
        import os
        full_env = {**os.environ, **env}
        proc = subprocess.run(
            cmd, cwd=REPO_ROOT, env=full_env,
            capture_output=True, text=True,
        )
        n = _count_collected(proc.stdout + proc.stderr)
        if n == 0 and proc.returncode not in (0, 5):  # 5 == no tests collected
            sys.stderr.write(proc.stdout + proc.stderr)
            sys.exit(f"ERROR: collection failed for suite '{label}' ({' '.join(paths)})")
        total += n
    return total


def update_declared(new_value: int) -> None:
    text = MATURITY.read_text()
    new_text = _OFFLINE_RE.sub(
        lambda m: f"{m.group('prefix')}{new_value}{m.group('rest')}", text, count=1
    )
    MATURITY.write_text(new_text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--update", action="store_true",
                    help="rewrite MATURITY.yaml offline_total to the collected count")
    args = ap.parse_args()

    declared = read_declared()
    actual = collect_actual()

    if args.update:
        if actual != declared:
            update_declared(actual)
            print(f"UPDATED MATURITY.yaml offline_total: {declared} -> {actual}")
        else:
            print(f"OK: offline_total already correct ({declared} collected tests)")
        return 0

    print(f"MATURITY.yaml offline_total (declared): {declared}")
    print(f"collected offline tests (actual):       {actual}")
    if actual == declared:
        print("OK: declared test count matches collected count.")
        return 0
    print(
        f"DRIFT: MATURITY.yaml declares {declared} offline tests but "
        f"{actual} are collected. Run `python tools/check_maturity.py --update` "
        f"(and align README references) to fix."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
