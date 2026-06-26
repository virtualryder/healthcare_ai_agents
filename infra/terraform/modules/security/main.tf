# HPP — Security module. KMS CMK, Bedrock Guardrail (PHI filters + unauthorized-
# determination denied topic), Cognito user pool carrying the custom:hpp_role
# claim the gateway authorizes on, and a least-privilege agent role. Terraform
# parity for infra/cloudformation/security.yaml.

variable "agent_id" { type = string }
variable "environment" { type = string }

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_region" "current" {}

resource "aws_kms_key" "agent" {
  description         = "CMK for HPP agent ${var.agent_id} (${var.environment}) - encrypts PHI-bearing audit + data"
  enable_key_rotation = true
}

resource "aws_kms_alias" "agent" {
  name          = "alias/hpp-${var.agent_id}-${var.environment}"
  target_key_id = aws_kms_key.agent.key_id
}

resource "aws_bedrock_guardrail" "phi" {
  name                      = "hpp-${var.agent_id}-${var.environment}"
  description               = "PHI masking, prompt-attack filter, and an unauthorized-determination denied topic for healthcare AI."
  blocked_input_messaging   = "I can't help with that request."
  blocked_outputs_messaging = "I can't provide that information."

  content_policy_config {
    filters_config {
      type            = "PROMPT_ATTACK"
      input_strength  = "HIGH"
      output_strength = "NONE"
    }
  }

  sensitive_information_policy_config {
    pii_entities_config {
      type   = "US_SOCIAL_SECURITY_NUMBER"
      action = "BLOCK"
    }
    pii_entities_config {
      type   = "US_BANK_ACCOUNT_NUMBER"
      action = "BLOCK"
    }
    pii_entities_config {
      type   = "CREDIT_DEBIT_CARD_NUMBER"
      action = "BLOCK"
    }
    pii_entities_config {
      type   = "NAME"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "ADDRESS"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "AGE"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "EMAIL"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "PHONE"
      action = "ANONYMIZE"
    }
  }

  topic_policy_config {
    topics_config {
      name       = "UnauthorizedCoverageOrClinicalDetermination"
      definition = "Issuing a binding coverage determination, medical-necessity denial, or clinical order the agent is not authorized to make. AI assists; a licensed human decides."
      type       = "DENY"
    }
  }
}

resource "aws_cognito_user_pool" "this" {
  name = "hpp-${var.agent_id}-${var.environment}"
  admin_create_user_config {
    allow_admin_create_user_only = true
  }
  schema {
    name                = "hpp_role"
    attribute_data_type = "String"
    mutable             = true
    string_attribute_constraints {
      min_length = 1
      max_length = 64
    }
  }
}

resource "aws_cognito_user_pool_client" "this" {
  name            = "hpp-${var.agent_id}-${var.environment}-app"
  user_pool_id    = aws_cognito_user_pool.this.id
  generate_secret = false
  explicit_auth_flows = ["ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
}

resource "aws_iam_role" "agent" {
  name = "hpp-${var.agent_id}-${var.environment}-agent"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = [
          "lambda.amazonaws.com", "states.amazonaws.com",
          "ecs-tasks.amazonaws.com", "bedrock-agentcore.amazonaws.com"
        ]
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "agent" {
  name = "least-privilege"
  role = aws_iam_role.agent.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel", "bedrock:ApplyGuardrail"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["kms:Decrypt", "kms:GenerateDataKey"]
        Resource = aws_kms_key.agent.arn
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:Query"]
        Resource = "arn:${data.aws_partition.current.partition}:dynamodb:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:table/hpp-${var.agent_id}-${var.environment}-*"
      }
    ]
  })
}

output "kms_key_arn" { value = aws_kms_key.agent.arn }
output "guardrail_id" { value = aws_bedrock_guardrail.phi.guardrail_id }
output "user_pool_id" { value = aws_cognito_user_pool.this.id }
output "user_pool_client_id" { value = aws_cognito_user_pool_client.this.id }
output "agent_role_arn" { value = aws_iam_role.agent.arn }
