# IAM — MISCONFIGURED: wildcard actions and resources
# CIS AWS 1.16: Ensure IAM policies that allow full administrative privileges are not attached (FAIL)
# checkov: CKV_AWS_40, CKV_AWS_274, CKV2_AWS_40

resource "aws_iam_policy" "meridian_app_policy" {
  name        = "meridian-app-policy"
  description = "Policy for Meridian application services"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # MISCONFIGURED: wildcard actions on all S3 resources
        Effect   = "Allow"
        Action   = ["s3:*"]
        Resource = "*"
      },
      {
        # MISCONFIGURED: wildcard on EC2 — allows instance termination, SG modification, etc.
        Effect   = "Allow"
        Action   = ["ec2:*"]
        Resource = "*"
      },
      {
        # MISCONFIGURED: allows passing any role — privilege escalation path
        Effect   = "Allow"
        Action   = ["iam:PassRole"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "meridian_lambda_role" {
  name = "meridian-lambda-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # MISCONFIGURED: overly broad trust policy — any principal can assume this role
        Effect    = "Allow"
        Principal = { "AWS" : "*" }
        Action    = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "meridian_lambda_admin" {
  role       = aws_iam_role.meridian_lambda_role.name
  # MISCONFIGURED: attaching AdministratorAccess to a Lambda execution role
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
