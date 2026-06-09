#!/usr/bin/env bash
# deploy.sh — Meridian Financial deployment script
# NOTE: Contains deliberately planted FAKE credentials for security training.
# The keys below are AWS documentation example keys — non-functional.

set -euo pipefail

# MISCONFIGURATION: hardcoded credentials in deployment script
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export AWS_DEFAULT_REGION="us-east-1"

echo "Deploying Meridian payment processor..."
# aws s3 sync dist/ s3://meridian-deployment-artifacts/
# aws lambda update-function-code --function-name meridian-payment --zip-file fileb://function.zip
echo "Deploy complete."
