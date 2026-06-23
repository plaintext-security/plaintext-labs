#!/usr/bin/env bash
# Seed the the target account multi-hop IAM privilege-escalation scenario.
# Path: dev-alice -> LambdaRole (sts:AssumeRole) -> AdminRole (iam:PassRole + lambda:UpdateFunctionConfiguration)
set -euo pipefail

echo "==> Seeding  IAM escalation scenario (module 03 — IAM Attack Paths)..."

# ---- Users ----
awslocal iam create-user --user-name dev-alice 2>/dev/null || true

# ---- dev-alice policy: can assume the Lambda role ----
awslocal iam create-policy \
  --policy-name AlicePolicy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "AssumeOnlyLambdaRole",
        "Effect": "Allow",
        "Action": "sts:AssumeRole",
        "Resource": "arn:aws:iam::000000000001:role/LambdaRole"
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
  --policy-arn arn:aws:iam::000000000001:policy/AlicePolicy 2>/dev/null || true

# ---- AdminRole: the escalation target ----
awslocal iam create-role \
  --role-name AdminRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::000000000001:root"},
      "Action": "sts:AssumeRole"
    }]
  }' 2>/dev/null || true

awslocal iam attach-role-policy \
  --role-name AdminRole \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess 2>/dev/null || true

# ---- LambdaRole: middle hop — has PassRole + UpdateFunctionConfiguration ----
awslocal iam create-role \
  --role-name LambdaRole \
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
  --policy-name LambdaPolicy \
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
  --role-name LambdaRole \
  --policy-arn arn:aws:iam::000000000001:policy/LambdaPolicy 2>/dev/null || true

echo "==> Seed complete. Escalation scenario ready."
echo "    Path: dev-alice -> LambdaRole (sts:AssumeRole)"
echo "          LambdaRole -> AdminRole (iam:PassRole + lambda:UpdateFunctionConfiguration)"
