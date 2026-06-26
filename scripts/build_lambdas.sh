#!/usr/bin/env bash
# Package the connector dispatcher (platform_core + agent connectors) into a Lambda zip
# with dependencies vendored in. Usage: scripts/build_lambdas.sh <AgentId>
set -euo pipefail
AGENT_ID="${1:-01-revenue-cycle-denial}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/.build/$AGENT_ID"
rm -rf "$BUILD" && mkdir -p "$BUILD"
cp -r "$ROOT/platform_core/hpp_agent_platform" "$BUILD/"
# (Add the agent's connectors/live.py adapters here before zipping.)
( cd "$BUILD" && zip -qr "$ROOT/.build/${AGENT_ID}-connector.zip" . )
echo "Built $ROOT/.build/${AGENT_ID}-connector.zip"
