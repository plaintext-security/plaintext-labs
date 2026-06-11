#!/usr/bin/env bash
# Seed: create the KMS key Meridian uses to protect data at rest.
set -euo pipefail

echo "==> Creating KMS key (module 17 — Data Protection & KMS)..."
KEY_ID=$(awslocal kms create-key \
  --description "Meridian data-at-rest key" \
  --query KeyMetadata.KeyId --output text)
awslocal kms create-alias --alias-name alias/meridian-data --target-key-id "$KEY_ID" 2>/dev/null || true
echo "$KEY_ID" > /lab/data/key-id.txt
echo "==> KMS key ready: $KEY_ID  (alias/meridian-data)"
