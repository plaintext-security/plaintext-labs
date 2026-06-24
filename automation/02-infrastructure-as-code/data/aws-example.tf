# AWS cloud example — for learners with an AWS account.
# This file is NOT active by default; rename to aws-example.tf.disabled if you want to
# prevent it from being planned alongside main.tf.
#
# Prerequisites: AWS credentials configured in environment (AWS_ACCESS_KEY_ID, etc.)
# WARNING: running tofu apply creates real, billable AWS resources.

# Uncomment and configure if you have AWS access:

# terraform {
#   required_providers {
#     aws = {
#       source  = "hashicorp/aws"
#       version = "~> 5.0"
#     }
#   }
# }
#
# provider "aws" {
#   region = "us-east-1"
# }
#
# resource "aws_s3_bucket" "security_assets" {
#   bucket = "security-assets-${var.env_name}"
#   tags = {
#     Environment = var.env_name
#     ManagedBy   = "opentofu"
#   }
# }
#
# resource "aws_s3_bucket_versioning" "security_assets" {
#   bucket = aws_s3_bucket.security_assets.id
#   versioning_configuration {
#     status = "Enabled"
#   }
# }
