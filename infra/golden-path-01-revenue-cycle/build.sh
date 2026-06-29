#!/usr/bin/env bash
# Vendor platform_core into the Lambda build context, then build + deploy in one go.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
rm -rf "$HERE/src/hpp_agent_platform"
cp -r "$HERE/../../platform_core/hpp_agent_platform" "$HERE/src/hpp_agent_platform"
cd "$HERE"
sam build
echo "Built. Deploy with:  sam deploy --guided   (first time) or  sam deploy"
