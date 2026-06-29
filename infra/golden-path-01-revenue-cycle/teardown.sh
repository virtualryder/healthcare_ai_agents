#!/usr/bin/env bash
# Tear down the golden path. Usage: ./teardown.sh <stack-name>
set -euo pipefail
STACK="${1:-hpp-gp01-dev}"
sam delete --stack-name "$STACK" --no-prompts || aws cloudformation delete-stack --stack-name "$STACK"
echo "Requested deletion of $STACK. (Audit data in DynamoDB PITR / any WORM snapshots persist per retention.)"
