#!/usr/bin/env bash
# data/setup.sh — deploy the vulnerable Lambda to LocalStack and seed supporting resources.
# Called by `make up` after LocalStack is healthy.
set -euo pipefail

ENDPOINT="http://localstack:4566"
REGION="us-east-1"
AL="awslocal --endpoint-url $ENDPOINT --region $REGION"

echo "== Seeding  serverless environment =="

# Create the IAM role
echo "[1/4] Creating over-privileged IAM role..."
$AL iam create-role \
  --role-name notifier-role \
  --assume-role-policy-document '{
    "Version":"2012-10-17",
    "Statement":[
      {"Effect":"Allow","Principal":{"AWS":"*"},"Action":"sts:AssumeRole"},
      {"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}
    ]
  }' 2>/dev/null || true

$AL iam put-role-policy \
  --role-name notifier-role \
  --policy-name NotifierPolicy \
  --policy-document '{
    "Version":"2012-10-17",
    "Statement":[
      {"Effect":"Allow","Action":"s3:*","Resource":"*"},
      {"Effect":"Allow","Action":"iam:*","Resource":"*"},
      {"Effect":"Allow","Action":"sts:AssumeRole","Resource":"*"},
      {"Effect":"Allow","Action":["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],"Resource":"arn:aws:logs:*:*:*"}
    ]
  }' 2>/dev/null || true

echo "   -> IAM role notifier-role created with wildcard policies"

# Package and deploy the Lambda
echo "[2/4] Packaging Lambda function..."
cd /lab/data/lambda
zip -q /tmp/notifier.zip handler.py

echo "[3/4] Deploying Lambda to LocalStack..."
ROLE_ARN="arn:aws:iam::000000000000:role/notifier-role"

$AL lambda create-function \
  --function-name notifier \
  --runtime python3.12 \
  --handler handler.lambda_handler \
  --role "$ROLE_ARN" \
  --zip-file fileb:///tmp/notifier.zip \
  --environment 'Variables={
    APP_API_KEY=mrd_live_sk_EXAMPLEKEY1234567890abcdef,
    DB_CONNECTION_STRING=postgresql://appuser:db-password-example@db.internal..example/payments,
    ENVIRONMENT=production,
    INPUT_VALIDATION=false
  }' \
  --timeout 30 \
  2>/dev/null || \
  $AL lambda update-function-code \
    --function-name notifier \
    --zip-file fileb:///tmp/notifier.zip \
    2>/dev/null || true

echo "   -> Lambda notifier deployed"

# Create an S3 bucket for the data exfil demonstration
echo "[4/4] Creating exfil target S3 bucket..."
$AL s3api create-bucket --bucket sensitive-records --region $REGION 2>/dev/null || true
$AL s3 cp /dev/stdin s3://sensitive-records/customer-data.csv <<'CSV'
customer_id,name,account_number,balance
C001,Alice Chen,ACC-0001234,142500.00
C002,Bob Marsh,ACC-0001235,87300.50
CSV
echo "   -> S3 bucket sensitive-records seeded"

echo ""
echo "== Setup complete. Deployed resources:"
echo "   Lambda: notifier"
echo "   Role:   notifier-role (over-privileged: s3:*, iam:*, sts:AssumeRole *)"
echo "   S3:     sensitive-records (reachable via the Lambda's role)"
echo ""
echo "Test with:"
echo "  awslocal lambda invoke --function-name notifier \\"
echo '    --payload '"'"'{"account_id":"ACC-001","event_type":"payment"}'"'"' /tmp/response.json'
