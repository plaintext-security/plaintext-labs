#!/usr/bin/env bash
# Envelope encryption with KMS: KMS never sees your data, only wraps the data key.
#   generate-data-key -> get a plaintext key + a KMS-wrapped copy
#   encrypt data locally with the plaintext key, then throw the plaintext key away
#   store ciphertext + the wrapped key; only KMS can unwrap it to decrypt
set -euo pipefail
KEY_ID=$(cat /lab/data/key-id.txt)
WORK=/tmp/envelope; mkdir -p "$WORK"

echo "== The data we must protect at rest =="
printf 'ACCOUNT=ACC-001\nBALANCE=999999.00\nSSN=000-00-0001\n' | tee "$WORK/secret.txt"
echo

echo "== 1. Ask KMS for a data key — it returns the key in plaintext AND KMS-wrapped =="
awslocal kms generate-data-key --key-id "$KEY_ID" --key-spec AES_256 \
  --query '[Plaintext,CiphertextBlob]' --output text > "$WORK/datakey.b64"
cut -f1 "$WORK/datakey.b64" | base64 -d > "$WORK/datakey.bin"   # plaintext key (transient)
cut -f2 "$WORK/datakey.b64" | base64 -d > "$WORK/datakey.wrapped"  # KMS-wrapped key (we keep this)
echo "  got a 256-bit data key (plaintext, transient) + its KMS-wrapped form (persisted)"
echo

echo "== 2. Encrypt the data locally with the plaintext data key (KMS never sees the data) =="
openssl enc -aes-256-cbc -pbkdf2 -salt -in "$WORK/secret.txt" \
  -out "$WORK/secret.enc" -pass "file:$WORK/datakey.bin"
echo "  wrote secret.enc"
echo

echo "== 3. Destroy the plaintext data key — keep only ciphertext + wrapped key =="
shred -u "$WORK/datakey.bin" "$WORK/datakey.b64" 2>/dev/null || rm -f "$WORK/datakey.bin" "$WORK/datakey.b64"
echo "  on disk now: secret.enc (ciphertext) + datakey.wrapped (useless without KMS)"
echo

echo "== 4. Decrypt: ask KMS to UNWRAP the data key, then decrypt locally =="
awslocal kms decrypt --ciphertext-blob "fileb://$WORK/datakey.wrapped" \
  --query Plaintext --output text | base64 -d > "$WORK/datakey.bin"
openssl enc -d -aes-256-cbc -pbkdf2 -in "$WORK/secret.enc" \
  -out "$WORK/secret.dec" -pass "file:$WORK/datakey.bin"
shred -u "$WORK/datakey.bin" 2>/dev/null || rm -f "$WORK/datakey.bin"
echo "  recovered plaintext:"
sed 's/^/    /' "$WORK/secret.dec"
echo
echo "Takeaway: revoke the app's kms:Decrypt and the wrapped key — and every backup of it — is"
echo "permanently unreadable. Key access, not file deletion, is the real off-switch for data at rest."
