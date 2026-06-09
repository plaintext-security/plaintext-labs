# S3 — MISCONFIGURED: no encryption, no versioning, public access not blocked
# CIS AWS 2.1.1: Ensure all S3 buckets employ encryption-at-rest (FAIL)
# CIS AWS 2.1.5: Ensure that S3 Buckets are configured with Block public access (FAIL)
# checkov: CKV_AWS_18, CKV_AWS_19, CKV_AWS_21, CKV_AWS_144, CKV2_AWS_6

resource "aws_s3_bucket" "meridian_data" {
  bucket = "meridian-financial-data-lake"

  tags = {
    Name = "meridian-data-lake"
    # Missing: Owner, Environment, CostCenter tags
  }
}

# Missing: aws_s3_bucket_server_side_encryption_configuration
# Missing: aws_s3_bucket_versioning
# Missing: aws_s3_bucket_public_access_block
# Missing: aws_s3_bucket_logging

resource "aws_s3_bucket" "meridian_reports" {
  bucket = "meridian-financial-reports"
  # No ACL block — defaults to private but no explicit block_public_access
}

# Missing aws_s3_bucket_public_access_block for meridian_reports
