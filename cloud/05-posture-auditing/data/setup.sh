#!/usr/bin/env bash
# data/setup.sh — seed a deliberately misconfigured LocalStack AWS account.
# Run via: docker compose run --rm lab bash data/setup.sh
# All resources use fake/example credentials — no real AWS account needed.
set -euo pipefail

ENDPOINT="http://localstack:4566"
REGION="us-east-1"
ALIAS="awslocal --endpoint-url $ENDPOINT --region $REGION"

echo "== Seeding misconfigured Meridian-Inherited account =="

# ----- S3: public bucket (CIS 2.1.5, T1530) ----------------------------------
echo "[1/5] Creating public S3 bucket..."
$ALIAS s3api create-bucket --bucket meridian-inherited-public-data \
  --region $REGION 2>/dev/null || true

# Disable all block-public-access settings
$ALIAS s3api put-public-access-block \
  --bucket meridian-inherited-public-data \
  --public-access-block-configuration \
    BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false

# Apply public-read ACL
$ALIAS s3api put-bucket-acl \
  --bucket meridian-inherited-public-data \
  --acl public-read

# Drop a plausible-looking file in it
$ALIAS s3 cp /dev/stdin s3://meridian-inherited-public-data/employee-list.csv <<'CSV'
employee_id,name,email,department
1001,Alice Chen,alice@meridian.example,Engineering
1002,Bob Marsh,bob@meridian.example,Finance
CSV

echo "   -> bucket meridian-inherited-public-data is public (T1530)"

# ----- Security Group: 0.0.0.0/0 on SSH and RDP (CIS 5.2, T1021) ------------
echo "[2/5] Creating over-permissive security group..."
SG_ID=$($ALIAS ec2 create-security-group \
  --group-name meridian-wide-open \
  --description "Temporary SG — never cleaned up" \
  --output text --query 'GroupId' 2>/dev/null || \
  $ALIAS ec2 describe-security-groups \
    --filters Name=group-name,Values=meridian-wide-open \
    --query 'SecurityGroups[0].GroupId' --output text)

$ALIAS ec2 authorize-security-group-ingress \
  --group-id "$SG_ID" \
  --ip-permissions \
    IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges='[{CidrIp=0.0.0.0/0,Description="temp"}]' \
    IpProtocol=tcp,FromPort=3389,ToPort=3389,IpRanges='[{CidrIp=0.0.0.0/0}]' \
  2>/dev/null || true

echo "   -> security group $SG_ID allows 0.0.0.0/0:22 and 0.0.0.0/0:3389 (T1021)"

# ----- IAM: access key that has never been rotated (CIS 1.14) ----------------
echo "[3/5] Creating IAM user with stale access key..."
$ALIAS iam create-user --user-name meridian-svc-legacy 2>/dev/null || true
$ALIAS iam create-access-key --user-name meridian-svc-legacy \
  --output json > /tmp/legacy-key.json 2>/dev/null || true

echo "   -> IAM user meridian-svc-legacy has an access key (never rotated)"

# ----- CloudTrail: trail exists but logging is disabled (CIS 3.1) ------------
echo "[4/5] Creating CloudTrail trail with logging off..."
$ALIAS s3api create-bucket --bucket meridian-cloudtrail-logs \
  --region $REGION 2>/dev/null || true

$ALIAS cloudtrail create-trail \
  --name meridian-trail \
  --s3-bucket-name meridian-cloudtrail-logs \
  2>/dev/null || true
# Do NOT call start-logging — trail exists but is inactive
echo "   -> CloudTrail trail created but logging is NOT started (CIS 3.1)"

# ----- IAM: root account with no MFA (CIS 1.5) — simulated via account alias -
echo "[5/5] Simulating root account with no MFA (account alias)..."
$ALIAS iam create-account-alias --account-alias meridian-inherited 2>/dev/null || true
echo "   -> Root MFA check will fail (LocalStack simulates no-MFA state)"

echo ""
echo "== Setup complete. Misconfigured resources:"
echo "   S3:           meridian-inherited-public-data  (public ACL)"
echo "   Security Group: $SG_ID  (0.0.0.0/0 on 22, 3389)"
echo "   IAM User:     meridian-svc-legacy  (stale access key)"
echo "   CloudTrail:   meridian-trail  (logging disabled)"
echo "   Root MFA:     disabled (simulated)"
