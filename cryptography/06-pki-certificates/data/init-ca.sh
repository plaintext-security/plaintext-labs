#!/bin/bash
# Initialize the step-ca CA and issue a leaf certificate
set -e

export STEPPATH=/home/step/.step

# Lab-only CA password. step (>=0.28) requires a non-empty password file for the CA
# keys and provisioner; /dev/null is rejected and falls back to an interactive prompt.
PASS_FILE=/tmp/ca-password.txt
echo "corp-lab-ca-password" > "$PASS_FILE"

echo "=== Initializing Corp Private CA ==="
echo ""

# Start from a clean state so re-running the demo is idempotent: stop any step-ca
# left running from a previous run (it would still hold :8443) and wipe the old PKI.
CA_PID_FILE=/tmp/step-ca.pid
[ -f "$CA_PID_FILE" ] && kill "$(cat "$CA_PID_FILE")" 2>/dev/null || true
sleep 1
rm -rf "$STEPPATH"

# Initialize the CA (non-interactive)
step ca init \
  --name "Corp Internal CA" \
  --dns "localhost,ca.corp.internal" \
  --address ":8443" \
  --provisioner "admin@corp.internal" \
  --password-file "$PASS_FILE" \
  --provisioner-password-file "$PASS_FILE" \
  --no-db

echo "CA initialized at $STEPPATH"
echo ""

# Start step-ca in background
step-ca --password-file "$PASS_FILE" $STEPPATH/config/ca.json &
CA_PID=$!
echo "$CA_PID" > "$CA_PID_FILE"
sleep 3

echo "CA running (PID $CA_PID)"
echo ""

# Issue a leaf certificate
echo "=== Issuing leaf certificate for corp.internal ==="
step ca certificate \
  corp.internal \
  /tmp/leaf.crt \
  /tmp/leaf.key \
  --provisioner "admin@corp.internal" \
  --provisioner-password-file "$PASS_FILE" \
  --not-after 24h \
  --ca-url https://localhost:8443 \
  --root $STEPPATH/certs/root_ca.crt

echo ""
echo "=== Leaf certificate details ==="
step certificate inspect /tmp/leaf.crt --short

echo ""
echo "=== Verifying certificate chain ==="
step certificate verify /tmp/leaf.crt --roots $STEPPATH/certs/root_ca.crt
echo "Chain verification: PASSED"

echo ""
echo "CA PID: $CA_PID — kill $CA_PID to stop the CA"
