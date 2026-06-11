#!/usr/bin/env bash
# Fetch the client's SVID and make an mTLS call to the backend, presenting it.
# Success = the TLS handshake verifies BOTH ends and the backend's SPIFFE ID is
# what we expect. This is the whole point: each side proves its identity to the
# other with a cert it fetched at runtime, no shared secret.
set -uo pipefail

SOCK="/run/spire/sockets/agent.sock"
SVID_DIR="/tmp/svid"
mkdir -p "$SVID_DIR"

echo "[client] fetching our SVID ..."
if ! spire-agent api fetch x509 -socketPath "$SOCK" -write "$SVID_DIR" >/dev/null 2>&1; then
  echo "[client] !! no SVID issued — the Workload API refused us. Cannot do mTLS."
  exit 2
fi
echo "[client] our identity:"
spire-agent api fetch x509 -socketPath "$SOCK" 2>/dev/null | grep -i "SPIFFE ID" || true

echo "[client] connecting to backend:8443 with mutual TLS ..."
OUT="$(printf 'GET / HTTP/1.0\r\n\r\n' | \
  openssl s_client -connect backend:8443 -quiet \
    -cert   "${SVID_DIR}/svid.0.pem" \
    -key    "${SVID_DIR}/svid.0.key" \
    -CAfile "${SVID_DIR}/bundle.0.pem" 2>&1)"

echo "$OUT" | grep -E "Verify return code|hello from spiffe|subject=|depth=" || true
if echo "$OUT" | grep -q "hello from spiffe://meridian.local/backend"; then
  echo "[client] ✅ mutual TLS succeeded — both ends presented a valid SVID."
  exit 0
fi
echo "[client] ❌ mTLS did not complete as expected (see output above)."
exit 1
