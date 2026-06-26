# HPP — Agent service module. native = Step Functions + Lambda with a
# waitForTaskToken HITL gate (the reviewer approval resumes the machine);
# container = ECS Fargate / AgentCore Runtime (deployed separately). Terraform
# parity for infra/cloudformation/agent-service.yaml.

variable "agent_id" { type = string }
variable "environment" { type = string }
variable "deploy_mode" {
  type    = string
  default = "native"
}
variable "agent_role_arn" { type = string }
variable "hitl_table_name" {
  type    = string
  default = ""
}

data "aws_partition" "current" {}

resource "aws_sfn_state_machine" "agent" {
  count    = var.deploy_mode == "native" ? 1 : 0
  name     = "hpp-${var.agent_id}-${var.environment}"
  role_arn = var.agent_role_arn
  definition = jsonencode({
    Comment = "HPP ${var.agent_id} - deterministic core + Bedrock drafting + waitForTaskToken HITL. Deploy the full ASL from aws-native-reference/${var.agent_id}/stepfunctions/."
    StartAt = "LoadAndAnalyze"
    States = {
      LoadAndAnalyze = {
        Type    = "Pass"
        Comment = "deterministic core Lambda tasks (load -> analyze -> assemble -> draft -> compliance_check)"
        Next    = "HumanReviewGate"
      }
      HumanReviewGate = {
        Type     = "Task"
        Resource = "arn:${data.aws_partition.current.partition}:states:::lambda:invoke.waitForTaskToken"
        Comment  = "Blocks until a verified reviewer approves; mirrors interrupt_before in the LangGraph build."
        Parameters = {
          FunctionName = "hpp-${var.agent_id}-${var.environment}-connector"
          Payload = {
            "taskToken.$" = "$$.Task.Token"
            hitlTable     = var.hitl_table_name
          }
        }
        Next = "Finalize"
      }
      Finalize = {
        Type    = "Pass"
        Comment = "commit approved action / forward recommendation; write PHI-masked audit"
        End     = true
      }
    }
  })
}

output "state_machine_arn" {
  value = var.deploy_mode == "native" ? aws_sfn_state_machine.agent[0].arn : ""
}
