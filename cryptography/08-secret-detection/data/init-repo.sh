#!/bin/bash
# Initialize a seed git repository with planted fake credentials
# All credentials are in FAKE/test format — not real secrets.
set -e

REPO_DIR=/lab/data/repo
rm -rf "$REPO_DIR"
mkdir -p "$REPO_DIR"
cd "$REPO_DIR"

git init
git config user.email "dev@corp.internal"
git config user.name "Corp Developer"

# Commit 1: Initial application code (clean)
mkdir -p src
cat > src/app.py << 'EOF'
"""Corp Payroll API"""
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/payroll")
API_BASE_URL = "https://api.corp.internal"

def get_db_connection():
    return DATABASE_URL
EOF

cat > README.md << 'EOF'
# Corp Payroll API
Internal payroll calculation service.
EOF

git add .
git commit -m "Initial commit: payroll API skeleton"

# Commit 2: Add configuration with PLANTED FAKE credentials
# These are fake/test credentials in recognizable formats — not real keys
cat > src/config.py << 'EOF'
"""
Application configuration
WARNING: These credentials were accidentally committed and have been rotated.
"""

# AWS credentials (FAKE - these are test credentials in AKIA format)
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# Database (plaintext password — should use Vault)
DATABASE_PASSWORD = "Corp$DB!Pass2026"

# Internal API key
INTERNAL_API_KEY = "sk-corp-internal-12345abcdef"
EOF

git add .
git commit -m "Add configuration (temporary hardcoded values for testing)"

# Commit 3: "Fix" — remove credentials (but they persist in history!)
cat > src/config.py << 'EOF'
"""Application configuration — credentials removed, use environment variables."""
import os

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", "")
INTERNAL_API_KEY = os.environ.get("INTERNAL_API_KEY", "")
EOF

git add .
git commit -m "Remove hardcoded credentials — use environment variables"

# Commit 4: Add more application code (clean)
cat > src/payroll.py << 'EOF'
"""Payroll calculation module"""

def calculate_gross(salary, hours_worked, hourly_rate=None):
    if hourly_rate:
        return hours_worked * hourly_rate
    return salary / 12  # Monthly

def calculate_net(gross, tax_rate=0.25):
    return gross * (1 - tax_rate)
EOF

git add .
git commit -m "Add payroll calculation module"

echo ""
echo "Seed repository initialized at $REPO_DIR"
echo "Commit history:"
git log --oneline
echo ""
echo "The fake AWS key (AKIAIOSFODNN7EXAMPLE) is in commit history even though it was 'removed'."
