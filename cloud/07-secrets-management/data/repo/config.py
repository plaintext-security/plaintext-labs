# config.py — the target account app configuration
# Credentials removed — use environment variables or a secrets manager.

import os

# Application configuration
APP_NAME = "payment-processor"
ENVIRONMENT = "production"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Database
DB_HOST = os.environ.get("DB_HOST", "db.internal..example")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_NAME = os.environ.get("DB_NAME", "_payments")

# AWS credentials — loaded from environment (IAM role or secrets manager)
# Do not hardcode credentials here. See docs/secrets-management.md.
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# S3 bucket for payment records
PAYMENT_RECORDS_BUCKET = "payment-records-prod"
