#!/usr/bin/env bash
# Seed the LocalStack environment with the Meridian Financial account configuration.
# Called automatically by `make up` via docker-compose.
set -euo pipefail

echo "==> Seeding Meridian Financial IAM configuration in LocalStack..."

ENDPOINT="--endpoint-url http://localstack:4566"
ACCOUNT_ID="000000000001"

# ----- Users -----
awslocal iam create-user --user-name admin-svc 2>/dev/null || true
awslocal iam create-user --user-name dev-alice 2>/dev/null || true

# Attach AWS-managed AdministratorAccess to admin-svc
awslocal iam attach-user-policy \
  --user-name admin-svc \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess 2>/dev/null || true

# ----- Custom over-broad developer policy -----
awslocal iam create-policy \
  --policy-name MeridianDevPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "S3FullAccess",
        "Effect": "Allow",
        "Action": "s3:*",
        "Resource": "*"
      },
      {
        "Sid": "EC2Describe",
        "Effect": "Allow",
        "Action": ["ec2:Describe*", "ec2:List*"],
        "Resource": "*"
      },
      {
        "Sid": "IAMPassRole",
        "Effect": "Allow",
        "Action": "iam:PassRole",
        "Resource": "*"
      }
    ]
  }' 2>/dev/null || true

POLICY_ARN="arn:aws:iam::000000000001:policy/MeridianDevPolicy"

awslocal iam attach-user-policy \
  --user-name dev-alice \
  --policy-arn "$POLICY_ARN" 2>/dev/null || true

# ----- EC2 instance role -----
awslocal iam create-role \
  --role-name MeridianEC2InstanceRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' 2>/dev/null || true

awslocal iam attach-role-policy \
  --role-name MeridianEC2InstanceRole \
  --policy-arn "$POLICY_ARN" 2>/dev/null || true

awslocal iam attach-role-policy \
  --role-name MeridianEC2InstanceRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore 2>/dev/null || true

awslocal iam create-instance-profile \
  --instance-profile-name MeridianEC2InstanceProfile 2>/dev/null || true

awslocal iam add-role-to-instance-profile \
  --instance-profile-name MeridianEC2InstanceProfile \
  --role-name MeridianEC2InstanceRole 2>/dev/null || true

# ----- S3 bucket with public access (misconfigured) -----
awslocal s3api create-bucket \
  --bucket meridian-uploads-dev \
  --region us-east-1 2>/dev/null || true

# Disable all public-access-block settings (misconfiguration)
awslocal s3api put-public-access-block \
  --bucket meridian-uploads-dev \
  --public-access-block-configuration \
    'BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false' 2>/dev/null || true

# Add a public READ ACL grant
awslocal s3api put-bucket-acl \
  --bucket meridian-uploads-dev \
  --acl public-read 2>/dev/null || true

echo "==> Seed complete. Account is ready for enumeration."
