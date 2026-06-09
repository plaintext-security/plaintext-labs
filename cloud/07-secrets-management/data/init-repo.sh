#!/usr/bin/env bash
# data/init-repo.sh — build the seed git repository with planted credential history.
# Called by `make up`. Creates /lab/data/repo as a git repo with two commits:
#   1. config.py with a hardcoded fake AWS key (the misconfiguration)
#   2. config.py with the key removed (the "fix" that doesn't actually fix it)
# trufflehog will find the key in commit 1 even though it's gone from commit 2.
set -euo pipefail

REPO="/lab/data/repo"

# If already initialised (e.g. make up run twice), skip
if [ -d "$REPO/.git" ]; then
  echo "data/repo already initialised — skipping"
  exit 0
fi

git init "$REPO"
git -C "$REPO" config user.email "meridian-dev@example.com"
git -C "$REPO" config user.name "Meridian Dev"

# ---- Commit 1: introduce the credential ----
cat > "$REPO/config.py" <<'PYEOF'
# config.py — Meridian Financial app configuration
# NOTE: This file contains a deliberately planted FAKE credential for security training.
# The key below is the AWS documentation example key — it is non-functional.

import os

APP_NAME = "meridian-payment-processor"
ENVIRONMENT = "production"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

DB_HOST = os.environ.get("DB_HOST", "db.internal.meridian.example")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "meridian_payments")

# AWS credentials — HARDCODED (this is the misconfiguration being demonstrated)
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
AWS_REGION = "us-east-1"

PAYMENT_RECORDS_BUCKET = "meridian-payment-records-prod"
PYEOF

cat > "$REPO/app.py" <<'PYEOF'
# app.py — Meridian Financial payment processor stub
import config

def process_payment(amount, account_id):
    return {"status": "processed", "amount": amount, "account_id": account_id}

if __name__ == "__main__":
    print(process_payment(100.00, "ACC-001"))
PYEOF

git -C "$REPO" add config.py app.py
git -C "$REPO" commit -m "Add payment processor config and app stub"

# ---- Commit 2: remove the credential (but it persists in history) ----
cat > "$REPO/config.py" <<'PYEOF'
# config.py — Meridian Financial app configuration
# Credentials removed — use environment variables or a secrets manager.

import os

APP_NAME = "meridian-payment-processor"
ENVIRONMENT = "production"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

DB_HOST = os.environ.get("DB_HOST", "db.internal.meridian.example")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "meridian_payments")

# AWS credentials — loaded from environment (IAM role or secrets manager)
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

PAYMENT_RECORDS_BUCKET = "meridian-payment-records-prod"
PYEOF

git -C "$REPO" add config.py
git -C "$REPO" commit -m "Remove hardcoded credentials — use env vars instead"

# ---- Commit 3: README ----
cat > "$REPO/README.md" <<'MDEOF'
# Meridian Payment Processor

Internal payment processing service. All configuration via environment variables.
Never hardcode credentials — use the IAM role or retrieve from Vault.
MDEOF

git -C "$REPO" add README.md
git -C "$REPO" commit -m "Add README"

echo "data/repo initialised with 3 commits (credential planted in commit 1, removed in commit 2)"
echo "Run: trufflehog git file:///lab/data/repo"
