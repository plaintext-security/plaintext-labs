# Cloud infrastructure — first draft (intentionally misconfigured for lab exercise)
# DO NOT apply to a real cloud account.
#
# Every misconfiguration below is a line of Terraform that, shipped, becomes a named real breach.
# The point of the scanner+gate you build is to catch each one in the diff before it deploys.

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

# Misconfiguration 1: S3 bucket with public ACL, no versioning, no access logging, no encryption
# Real-world anchor: the 2017 wave of public-S3-bucket leaks (Accenture, Verizon/Nice Systems,
# Booz Allen Hamilton, Dow Jones) — terabytes of sensitive data exposed by exactly this shape:
# a bucket left publicly readable. checkov: CKV_AWS_20 (public ACL), CKV_AWS_19 (encryption).
resource "aws_s3_bucket" "data_lake" {
  bucket = "data-lake"
  # Missing: server_side_encryption_configuration
  # Missing: versioning
  # Missing: logging
  tags = {
    Name = "data-lake"
  }
}

resource "aws_s3_bucket_acl" "data_lake_acl" {
  bucket = aws_s3_bucket.data_lake.id
  acl    = "public-read"  # Misconfiguration: public read access
}

# Misconfiguration 2: Security group open to the world on SSH
# Real-world anchor: the 2019 Capital One breach began with an over-permissive WAF/SG and an
# SSRF-to-IMDS pivot — internet-reachable ingress plus an over-broad instance role is the path.
# checkov: CKV_AWS_24 (0.0.0.0/0 on port 22).
resource "aws_security_group" "admin_sg" {
  name        = "admin"
  description = "Admin access"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Misconfiguration: open to internet
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Misconfiguration 3: EC2 instance with admin IAM role and no IMDSv2 requirement
# Real-world anchor: 2019 Capital One — the EC2 instance carried an over-broad role and IMDSv1 was
# reachable, so the SSRF could read instance credentials and list/exfil the S3 buckets. Enforcing
# IMDSv2 (http_tokens = "required") and least-privilege on the role each break that chain.
# checkov: CKV_AWS_290/CKV_AWS_355 (wildcard policy), CKV_AWS_79 (IMDSv2 not enforced).
resource "aws_iam_role" "admin_role" {
  name = "admin-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "admin_policy" {
  name = "admin-policy"
  role = aws_iam_role.admin_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action   = "*"        # Misconfiguration: wildcard actions
      Effect   = "Allow"
      Resource = "*"        # Misconfiguration: all resources
    }]
  })
}

resource "aws_instance" "bastion" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type          = "t3.micro"
  iam_instance_profile   = aws_iam_role.admin_role.name
  # Misconfiguration: missing metadata_options { http_tokens = "required" } (IMDSv2)
  # Misconfiguration: missing monitoring = true
  vpc_security_group_ids = [aws_security_group.admin_sg.id]

  tags = {
    Name = "bastion"
  }
}
