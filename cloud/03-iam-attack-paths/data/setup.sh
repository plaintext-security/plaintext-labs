#!/usr/bin/env bash
# Seed the Meridian Financial multi-hop IAM privilege-escalation scenario.
# Path: dev-alice -> MeridianLambdaRole (sts:AssumeRole) -> MeridianAdminRole (iam:PassRole + lambda:UpdateFunctionConfiguration)
set -euo pipefail

echo "==> Seeding Meridian IAM escalation scenario (module 03 — IAM Attack Paths)..."

# ---- Users ----
awslocal iam create-user --user-name dev-alice 2>/dev/null || true

# ---- dev-alice policy: can assume the Lambda role ----
awslocal iam create-policy \
  --policy-name MeridianAlicePolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "AssumeOnlyLambdaRole",
        "Effect": "Allow",
        "Action": "sts:AssumeRole",
        "Resource": "arn:aws:iam::000000000001:role/MeridianLambdaRole"
      },
      {
        "Sid": "ReadOnlyS3",
        "Effect": "Allow",
        "Action": ["s3:GetObject", "s3:ListBucket"],
        "Resource": "*"
      },
      {
        "Sid": "LambdaInvoke",
        "Effect": "Allow",
        "Action": ["lambda:InvokeFunction", "lambda:ListFunctions"],
        "Resource": "*"
      }
    ]
  }' 2>/dev/null || true

awslocal iam attach-user-policy \
  --user-name dev-alice \
  --policy-arn arn:aws:iam::000000000001:policy/MeridianAlicePolicy 2>/dev/null || true

# ---- MeridianAdminRole: the escalation target ----
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

# ---- MeridianLambdaRole: middle hop — has PassRole + UpdateFunctionConfiguration ----
awslocal iam create-role \
  --role-name MeridianLambdaRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
      },
      {
        "Effect": "Allow",
        "Principal": {"AWS": "arn:aws:iam::000000000001:user/dev-alice"},
        "Action": "sts:AssumeRole"
      }
    ]
  }' 2>/dev/null || true

awslocal iam create-policy \
  --policy-name MeridianLambdaPolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "PassAnyRole",
        "Effect": "Allow",
        "Action": "iam:PassRole",
        "Resource": "*"
      },
      {
        "Sid": "LambdaManage",
        "Effect": "Allow",
        "Action": [
          "lambda:UpdateFunctionConfiguration",
          "lambda:InvokeFunction",
          "lambda:GetFunction",
          "lambda:ListFunctions"
        ],
        "Resource": "*"
      },
      {
        "Sid": "Logs",
        "Effect": "Allow",
        "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        "Resource": "*"
      }
    ]
  }' 2>/dev/null || true

awslocal iam attach-role-policy \
  --role-name MeridianLambdaRole \
  --policy-arn arn:aws:iam::000000000001:policy/MeridianLambdaPolicy 2>/dev/null || true

echo "==> Seed complete. Escalation scenario ready."
echo "    Path: dev-alice -> MeridianLambdaRole (sts:AssumeRole)"
echo "          MeridianLambdaRole -> MeridianAdminRole (iam:PassRole + lambda:UpdateFunctionConfiguration)"
