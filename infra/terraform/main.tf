# HPP AI Agent Suite — Terraform parity for the CloudFormation quick-deploy.
# Provisions a customer-isolated, HIPAA-defensible per-agent environment:
# network (own VPC + in-account Bedrock endpoint + Flow Logs), security (KMS +
# Bedrock Guardrail + Cognito + least-privilege role), data (append-only audit +
# HITL + WORM), connectors (governed Lambda), the portable MCP gateway, and the
# agent (native Step Functions waitForTaskToken HITL | container).
#
# An AWS Business Associate Agreement must be in place before processing PHI.

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws     = { source = "hashicorp/aws", version = ">= 5.40" }
    archive = { source = "hashicorp/archive", version = ">= 2.4" }
  }
}

provider "aws" {
  region = var.region
}

module "network" {
  source      = "./modules/network"
  agent_id    = var.agent_id
  environment = var.environment
  vpc_cidr    = var.vpc_cidr
}

module "security" {
  source      = "./modules/security"
  agent_id    = var.agent_id
  environment = var.environment
}

module "data" {
  source               = "./modules/data"
  agent_id             = var.agent_id
  environment          = var.environment
  kms_key_arn          = module.security.kms_key_arn
  audit_retention_days = var.audit_retention_days
}

module "connectors" {
  source           = "./modules/connectors"
  agent_id         = var.agent_id
  environment      = var.environment
  kms_key_arn      = module.security.kms_key_arn
  audit_table_name = module.data.audit_table_name
  agent_role_arn   = module.security.agent_role_arn
}

module "gateway" {
  source              = "./modules/gateway"
  agent_id            = var.agent_id
  environment         = var.environment
  user_pool_id        = module.security.user_pool_id
  user_pool_client_id = module.security.user_pool_client_id
  connector_fn_arn    = module.connectors.connector_fn_arn
}

module "agent_service" {
  source          = "./modules/agent-service"
  agent_id        = var.agent_id
  environment     = var.environment
  deploy_mode     = var.deploy_mode
  agent_role_arn  = module.security.agent_role_arn
  hitl_table_name = module.data.hitl_table_name
}

output "vpc_id" { value = module.network.vpc_id }
output "guardrail_id" { value = module.security.guardrail_id }
output "audit_table" { value = module.data.audit_table_name }
output "worm_bucket" { value = module.data.worm_bucket_name }
output "gateway_url" { value = module.gateway.gateway_url }
output "state_machine_arn" { value = module.agent_service.state_machine_arn }
