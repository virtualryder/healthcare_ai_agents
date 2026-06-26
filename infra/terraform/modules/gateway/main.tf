# HPP — Gateway module (PORTABLE path: API Gateway HTTP API + Cognito JWT
# authorizer). Deploys in any commercial Region day one and routes every tool
# call to the governed connector Lambda. Terraform parity for
# infra/cloudformation/gateway-portable.yaml.
#
# AgentCore path: the Bedrock AgentCore Gateway + Identity variant is provided in
# infra/cloudformation/agentcore-gateway.yaml. The Terraform AWS provider did not
# expose stable AgentCore Gateway resources at build time; deploy that path via
# CloudFormation (or a null_resource shim) where AgentCore is standardized.

variable "agent_id" { type = string }
variable "environment" { type = string }
variable "user_pool_id" { type = string }
variable "user_pool_client_id" { type = string }
variable "connector_fn_arn" { type = string }

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_region" "current" {}

resource "aws_apigatewayv2_api" "gateway" {
  name          = "hpp-${var.agent_id}-${var.environment}-gateway"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_authorizer" "jwt" {
  api_id           = aws_apigatewayv2_api.gateway.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "cognito-jwt"
  jwt_configuration {
    audience = [var.user_pool_client_id]
    issuer   = "https://cognito-idp.${data.aws_region.current.name}.amazonaws.com/${var.user_pool_id}"
  }
}

resource "aws_apigatewayv2_integration" "tool" {
  api_id                 = aws_apigatewayv2_api.gateway.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.connector_fn_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "tool" {
  api_id             = aws_apigatewayv2_api.gateway.id
  route_key          = "POST /tool/{kind}/{method}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.jwt.id
  target             = "integrations/${aws_apigatewayv2_integration.tool.id}"
}

resource "aws_apigatewayv2_stage" "this" {
  api_id      = aws_apigatewayv2_api.gateway.id
  name        = var.environment
  auto_deploy = true
}

resource "aws_lambda_permission" "invoke" {
  statement_id  = "AllowApiGwInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.connector_fn_arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:${data.aws_partition.current.partition}:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${aws_apigatewayv2_api.gateway.id}/*/*/tool/*"
}

output "gateway_url" {
  value = "https://${aws_apigatewayv2_api.gateway.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${var.environment}"
}
