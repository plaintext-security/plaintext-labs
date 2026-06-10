#!/usr/bin/env bash
# Part 2: SOPS — encrypt a YAML config with an age key (values encrypted, keys visible).
set -euo pipefail

age-keygen -o /tmp/age-key.txt 2>/dev/null
pub=$(age-keygen -y /tmp/age-key.txt 2>/dev/null)

cat > /tmp/config.yml <<'EOF'
database:
  host: db.meridian.internal
  username: payroll_svc
  password: super-secret-password
api_key: sk-meridian-prod-12345
EOF

export SOPS_AGE_KEY_FILE=/tmp/age-key.txt
sops --encrypt --age "$pub" /tmp/config.yml > /tmp/config.enc.yml

echo "Encrypted config (values encrypted, keys visible):"
head -15 /tmp/config.enc.yml
echo ""
echo "Decrypted (original values):"
sops --decrypt /tmp/config.enc.yml
