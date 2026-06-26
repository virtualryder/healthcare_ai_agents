#!/usr/bin/env bash
# Stage nested CloudFormation templates to S3 and deploy the HPP quickstart stack.
# Usage: scripts/deploy.sh <AgentId> <Env> <GatewayMode> <DeployMode> <s3-base-uri>
set -euo pipefail
AGENT_ID="${1:-01-revenue-cycle-denial}"
ENV="${2:-dev}"
GW="${3:-portable}"
DEPLOY="${4:-native}"
S3_BASE="${5:?pass an s3://bucket/prefix to stage nested templates}"
VPC_CIDR="${6:-10.30.0.0/16}"

CFN_DIR="$(cd "$(dirname "$0")/../infra/cloudformation" && pwd)"
echo "Staging templates from $CFN_DIR to $S3_BASE ..."
aws s3 cp "$CFN_DIR/" "$S3_BASE/" --recursive --exclude "*" --include "*.yaml"

BUCKET="$(echo "$S3_BASE" | sed -E 's#s3://([^/]+)/.*#\1#')"
PREFIX="$(echo "$S3_BASE" | sed -E 's#s3://[^/]+/(.*)#\1#')"
BASE_URL="https://${BUCKET}.s3.amazonaws.com/${PREFIX}"

echo "Deploying hpp-${AGENT_ID}-${ENV} (gateway=${GW}, deploy=${DEPLOY}) ..."
aws cloudformation deploy \
  --template-file "$CFN_DIR/quickstart.yaml" \
  --stack-name "hpp-${AGENT_ID}-${ENV}" \
  --parameter-overrides AgentId="$AGENT_ID" Environment="$ENV" \
                        GatewayMode="$GW" DeployMode="$DEPLOY" \
                        TemplateBaseUrl="$BASE_URL" VpcCidr="$VPC_CIDR" \
  --capabilities CAPABILITY_NAMED_IAM
echo "Done. Outputs:"
aws cloudformation describe-stacks --stack-name "hpp-${AGENT_ID}-${ENV}" \
  --query "Stacks[0].Outputs" --output table
