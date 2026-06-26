# HPP — Data module. Append-only PHI-masked audit DynamoDB (PITR), HITL approvals
# table, and a WORM S3 Object Lock COMPLIANCE bucket. Terraform parity for
# infra/cloudformation/data.yaml. Append-only is enforced by an Org SCP / IAM
# policy denying dynamodb:UpdateItem & DeleteItem on the audit table (the agent
# role grants only PutItem/GetItem/Query).

variable "agent_id" { type = string }
variable "environment" { type = string }
variable "kms_key_arn" { type = string }
variable "audit_retention_days" {
  type    = number
  default = 2555 # 7 years; tune to the org records schedule
}

data "aws_caller_identity" "current" {}

resource "aws_dynamodb_table" "audit" {
  name         = "hpp-${var.agent_id}-${var.environment}-audit"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "audit_id"
  range_key    = "ts"

  attribute {
    name = "audit_id"
    type = "S"
  }
  attribute {
    name = "ts"
    type = "S"
  }
  point_in_time_recovery { enabled = true }
  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn
  }
}

resource "aws_dynamodb_table" "hitl" {
  name         = "hpp-${var.agent_id}-${var.environment}-hitl"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "review_id"

  attribute {
    name = "review_id"
    type = "S"
  }
  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn
  }
}

resource "aws_s3_bucket" "worm" {
  bucket              = "hpp-${var.agent_id}-${var.environment}-worm-${data.aws_caller_identity.current.account_id}"
  object_lock_enabled = true
}

resource "aws_s3_bucket_object_lock_configuration" "worm" {
  bucket = aws_s3_bucket.worm.id
  rule {
    default_retention {
      mode = "COMPLIANCE"
      days = var.audit_retention_days
    }
  }
}

resource "aws_s3_bucket_versioning" "worm" {
  bucket = aws_s3_bucket.worm.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "worm" {
  bucket = aws_s3_bucket.worm.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "worm" {
  bucket                  = aws_s3_bucket.worm.id
  block_public_acls       = true
  block_public_policy      = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "audit_table_name" { value = aws_dynamodb_table.audit.name }
output "hitl_table_name" { value = aws_dynamodb_table.hitl.name }
output "worm_bucket_name" { value = aws_s3_bucket.worm.id }
