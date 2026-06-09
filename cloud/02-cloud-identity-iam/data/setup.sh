#!/usr/bin/env bash
# Seed Meridian Financial misconfigured IAM environment for the cloudfox lab.
# Three principals: dev-alice (over-broad), ci-deploy role (loose trust), admin role.
set -euo pipefail

echo "==> Seeding Meridian IAM (module 02 — Cloud Identity & IAM)..."

# ---- Users ----
awslocal iam create-user --user-name dev-alice 2>/dev/null || true
awslocal iam create-user --user-name dev-bob   2>/dev/null || true

# ---- Over-broad developer policy ----
awslocal iam create-policy \
  --policy-name MeridianDevPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "S3All",
        "Effect": "Allow",
        "Action": "s3:*",
        "Resource": "*"
      },
      {
        "Sid": "EC2RunInstances",
        "Effect": "Allow",
        "Action": ["ec2:RunInstances", "ec2:DescribeInstances", "ec2:TerminateInstances"],
        "Resource": "*"
      },
      {
        "Sid": "PassAnyRole",
        "Effect": "Allow",
        "Action": "iam:PassRole",
        "Resource": "*"
      },
      {
        "Sid": "ListIAM",
        "Effect": "Allow",
        "Action": ["iam:List*", "iam:Get*"],
        "Resource": "*"
      }
    ]
  }' 2>/dev/null || true

DEV_POLICY_ARN="arn:aws:iam::000000000001:policy/MeridianDevPolicy"
awslocal iam attach-user-policy --user-name dev-alice --policy-arn "$DEV_POLICY_ARN" 2>/dev/null || true

# ---- Admin role (the escalation target) ----
awslocal iam create-role \
  --role-name MeridianAdminRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::000000000001:root"},
      "Action": "sts:AssumeRole"
    }]
  }' 2>/dev/null || true

awslocal iam attach-role-policy \
  --role-name MeridianAdminRole \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess 2>/dev/null || true

# ---- CI/CD deploy role (loose OIDC trust — any sub) ----
awslocal iam create-role \
  --role-name MeridianCICDRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Federated": "arn:aws:iam::000000000001:oidc-provider/token.actions.githubusercontent.com"},
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        }
      }
    }]
  }' 2>/dev/null || true
# Note: no sub condition — any GitHub Actions workflow can assume this role.

awslocal iam create-policy \
  --policy-name MeridianCICDPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "ECSDeployAll",
        "Effect": "Allow",
        "Action": ["ecs:*", "ecr:*", "s3:*", "iam:PassRole"],
        "Resource": "*"
      }
    ]
  }' 2>/dev/null || true

awslocal iam attach-role-policy \
  --role-name MeridianCICDRole \
  --policy-arn arn:aws:iam::000000000001:policy/MeridianCICDPolicy 2>/dev/null || true

# ---- EC2 instance role (escalation target via PassRole) ----
awslocal iam create-role \
  --role-name MeridianEC2AdminRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }' 2>/dev/null || true

awslocal iam attach-role-policy \
  --role-name MeridianEC2AdminRole \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess 2>/dev/null || true

echo "==> Seed complete. IAM environment ready for cloudfox enumeration."
