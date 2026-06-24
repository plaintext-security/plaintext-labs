#!/bin/bash
# Initialize the step-ca CA and issue a leaf certificate
set -e

export STEPPATH=/home/step/.step

echo "=== Initializing Corp Private CA ==="
echo ""

# Initialize the CA (non-interactive)
step ca init \
  --name "Corp Internal CA" \
  --dns "localhost,ca.corp.internal" \
  --address ":8443" \
  --provisioner "admin@corp.internal" \
  --password-file /dev/null \
  --no-db 2>/dev/null || true

echo "CA initialized at $STEPPATH"
echo ""

# Start step-ca in background
step-ca --password-file /dev/null $STEPPATH/config/ca.json &
CA_PID=$!
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
  --provisioner-password-file /dev/null \
  --not-after 24h \
  --ca-url https://localhost:8443 \
  --root $STEPPATH/certs/root_ca.crt 2>/dev/null

echo ""
echo "=== Leaf certificate details ==="
step certificate inspect /tmp/leaf.crt --short

echo ""
echo "=== Verifying certificate chain ==="
step certificate verify /tmp/leaf.crt --roots $STEPPATH/certs/root_ca.crt
echo "Chain verification: PASSED"

echo ""
echo "CA PID: $CA_PID — kill $CA_PID to stop the CA"
