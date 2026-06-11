#!/usr/bin/env bash
# The cloud-native variant: store a secret in AWS Secrets Manager (simulated by
# LocalStack) and author the least-privilege IAM policy that gates reading it.
# Runs in the lab container; `awslocal` targets the LocalStack container.
set -euo pipefail

echo "== Storing the app's DB secret in Secrets Manager =="
awslocal secretsmanager create-secret \
    --name meridian/app/db \
    --secret-string '{"username":"appuser","password":"rotate-me-via-secrets-manager"}' \
    >/dev/null 2>&1 || \
awslocal secretsmanager put-secret-value \
    --secret-id meridian/app/db \
    --secret-string '{"username":"appuser","password":"rotate-me-via-secrets-manager"}' >/dev/null

SECRET_ARN=$(awslocal secretsmanager describe-secret --secret-id meridian/app/db \
    --query ARN --output text)
echo "  secret ARN: ${SECRET_ARN}"

echo "== Authoring the least-privilege read policy (GetSecretValue on THIS secret only) =="
cat > /tmp/app-secret-ro.json <<JSON
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "secretsmanager:GetSecretValue",
    "Resource": "${SECRET_ARN}"
  }]
}
JSON
awslocal iam create-policy \
    --policy-name app-secret-ro \
    --policy-document file:///tmp/app-secret-ro.json >/dev/null 2>&1 \
    || echo "  (policy already exists)"

echo "== The app reads its secret at runtime (no hardcoded value) =="
awslocal secretsmanager get-secret-value --secret-id meridian/app/db \
    --query SecretString --output text

echo
echo "Note: LocalStack does not fully enforce IAM, so the read above is not *blocked* here —"
echo "the lesson is authoring the tight Resource-scoped policy that WOULD gate it in real AWS."
