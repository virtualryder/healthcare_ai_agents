variable "region" {
  type    = string
  default = "us-east-1"
}
variable "agent_id" {
  type    = string
  default = "01-revenue-cycle-denial"
}
variable "environment" {
  type    = string
  default = "dev"
}
variable "vpc_cidr" {
  type    = string
  default = "10.30.0.0/16"
}
variable "gateway_mode" {
  type    = string
  default = "portable" # portable | agentcore (agentcore via CloudFormation)
}
variable "deploy_mode" {
  type    = string
  default = "native" # native | container
}
variable "audit_retention_days" {
  type    = number
  default = 2555
}
