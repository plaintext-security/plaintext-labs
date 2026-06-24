# AI-generated Terraform (for adversarial review)
# Prompt: "Create a Terraform config for an S3 data bucket and an EC2 instance with admin access"
# DO NOT apply to a real cloud account — contains deliberate security misconfigurations for lab exercise.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Misconfiguration 1: S3 bucket — public ACL, no encryption, no versioning, no access logging
resource "aws_s3_bucket" "data_bucket" {
  bucket = "data-pipeline"
  tags = {
    Name = "data-pipeline"
    # Missing: Environment tag (often required by policy)
  }
}

resource "aws_s3_bucket_acl" "data_bucket_acl" {
  bucket = aws_s3_bucket.data_bucket.id
  acl    = "public-read"  # Misconfiguration: public read access
}

# This is the "access logging bucket" — it is a genuine false positive for access logging
# on itself (a logging bucket logging to itself causes an infinite loop).
resource "aws_s3_bucket" "access_logs" {
  bucket = "access-logs"
  # checkov:skip=CKV_AWS_18:This is the access logging bucket itself; logging it to itself causes infinite loop
  tags = { Name = "access-logs" }
}

# Misconfiguration 2: IAM role with wildcard actions (over-broad admin)
resource "aws_iam_role" "ec2_admin_role" {
  name = "ec2-admin"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "ec2_admin_policy" {
  name = "ec2-admin-policy"
  role = aws_iam_role.ec2_admin_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action   = "*"         # Misconfiguration: wildcard actions (full admin)
      Effect   = "Allow"
      Resource = "*"         # Misconfiguration: all resources
    }]
  })
}

# Misconfiguration 3: EC2 instance — no encryption, no IMDSv2, public IP enabled
resource "aws_instance" "app_server" {
  ami                         = "ami-0c55b159cbfafe1f0"
  instance_type               = "t3.medium"
  iam_instance_profile        = aws_iam_role.ec2_admin_role.name
  associate_public_ip_address = true  # Misconfiguration: public IP (debatable, but flagged)
  # Missing: metadata_options { http_tokens = "required" }  — IMDSv2 not enforced
  # Missing: monitoring = true

  root_block_device {
    volume_size = 20
    # Misconfiguration 4: EBS volume not encrypted
    encrypted   = false
  }

  tags = {
    Name = "app-server"
  }
}

# Misconfiguration 5: Security group — SSH open to internet
resource "aws_security_group" "app_sg" {
  name        = "app-sg"
  description = "App server security group"

  ingress {
    description = "SSH from anywhere"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Misconfiguration: SSH open to internet
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
