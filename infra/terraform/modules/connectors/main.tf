# HPP — Connectors module. One governed connector dispatcher Lambda is the only
# thing that talks to a system of record; the MCP gateway invokes it per
# authorized tool call. Terraform parity for infra/cloudformation/connectors.yaml.
# Replace the inline reference handler with hpp_agent_platform.connectors (live).

variable "agent_id" { type = string }
variable "environment" { type = string }
variable "kms_key_arn" { type = string }
variable "audit_table_name" { type = string }
variable "agent_role_arn" { type = string }

data "archive_file" "connector" {
  type        = "zip"
  output_path = "${path.module}/.build/connector-${var.agent_id}.zip"
  source {
    filename = "index.py"
    content  = <<-PY
      # Reference connector dispatcher. In production this packages
      # hpp_agent_platform.connectors (live adapters) and routes the
      # gateway-authorized {kind}.{method} call to the system of record.
      import json
      def handler(event, context):
          path = (event.get("pathParameters") or {})
          kind, method = path.get("kind"), path.get("method")
          body = json.loads(event.get("body") or "{}")
          return {"statusCode": 200,
                  "headers": {"Content-Type": "application/json"},
                  "body": json.dumps({"kind": kind, "method": method,
                                      "note": "reference connector; wire live adapters here",
                                      "echo": body})}
    PY
  }
}

resource "aws_lambda_function" "connector" {
  function_name    = "hpp-${var.agent_id}-${var.environment}-connector"
  runtime          = "python3.12"
  handler          = "index.handler"
  timeout          = 30
  memory_size      = 256
  role             = var.agent_role_arn
  kms_key_arn      = var.kms_key_arn
  filename         = data.archive_file.connector.output_path
  source_code_hash = data.archive_file.connector.output_base64sha256
  environment {
    variables = {
      AUDIT_TABLE    = var.audit_table_name
      CONNECTOR_MODE = "live"
    }
  }
}

resource "aws_cloudwatch_log_group" "connector" {
  name              = "/aws/lambda/hpp-${var.agent_id}-${var.environment}-connector"
  retention_in_days = 365
}

output "connector_fn_arn" { value = aws_lambda_function.connector.arn }
output "connector_fn_name" { value = aws_lambda_function.connector.function_name }
