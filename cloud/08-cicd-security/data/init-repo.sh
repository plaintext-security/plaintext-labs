#!/usr/bin/env bash
# data/init-repo.sh — build the seed git repository with planted credentials.
# Called by `make up`. Creates /lab/data/repo as a git repo with a commit
# containing a fake AWS key in deploy.sh and a fake private key in terraform.tfvars.
# gitleaks will find both patterns.
set -euo pipefail

REPO="/lab/data/repo"

if [ -d "$REPO/.git" ]; then
  echo "data/repo already initialised — skipping"
  exit 0
fi

git init "$REPO"
git -C "$REPO" config user.email "meridian-ci@example.com"
git -C "$REPO" config user.name "Meridian CI"

cat > "$REPO/deploy.sh" <<'SHEOF'
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
echo "Deploy complete."
SHEOF

cat > "$REPO/terraform.tfvars" <<'TFEOF'
# terraform.tfvars — Meridian infrastructure variables
# NOTE: Contains a deliberately planted FAKE private key pattern for security training.

environment = "production"
region      = "us-east-1"

# MISCONFIGURATION: private key pattern in variables file
db_admin_private_key = <<EOT
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Z3VS5JJcds3xHn/ygWep4PAtEsHAMcBWFJKBqgBXIQkXmPY
EXAMPLE-FAKE-KEY-FOR-TRAINING-PURPOSES-ONLY-NOT-A-REAL-PRIVATE-KEY=
-----END RSA PRIVATE KEY-----
EOT

db_instance_class = "db.t3.medium"
TFEOF

git -C "$REPO" add deploy.sh terraform.tfvars
git -C "$REPO" commit -m "Initial deployment scripts and terraform config"

echo "data/repo initialised with planted credentials"
echo "Run: gitleaks detect --source /lab/data/repo --report-format json"
