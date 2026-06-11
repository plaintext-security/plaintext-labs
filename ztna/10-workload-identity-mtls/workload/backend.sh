#!/usr/bin/env bash
# backend workload: fetch our own SVID off the Workload API, then run an mTLS
# server that ONLY accepts a peer presenting a valid SVID from our trust domain.
# No key is baked into the image — the identity is fetched at runtime and rotates.
set -uo pipefail

SOCK="/run/spire/sockets/agent.sock"
SVID_DIR="/tmp/svid"
mkdir -p "$SVID_DIR"

echo "[backend] fetching SVID from the Workload API ..."
until spire-agent api fetch x509 -socketPath "$SOCK" -write "$SVID_DIR" >/dev/null 2>&1; do
  echo "[backend] no SVID yet (agent attesting?) — retrying ..."
  sleep 2
done

echo "[backend] got an identity:"
spire-agent api fetch x509 -socketPath "$SOCK" 2>/dev/null | grep -i "SPIFFE ID" || true

# mTLS server: -Verify 1 REQUIRES the client to present a cert that chains to our
# trust bundle. A peer with no SVID (unregistered) cannot complete the handshake.
echo "[backend] starting mTLS server on :8443 (client SVID required) ..."
while true; do
  printf 'HTTP/1.0 200 OK\r\n\r\nhello from spiffe://meridian.local/backend\r\n' | \
  openssl s_server -accept 8443 -quiet \
    -cert   "${SVID_DIR}/svid.0.pem" \
    -key    "${SVID_DIR}/svid.0.key" \
    -CAfile "${SVID_DIR}/bundle.0.pem" \
    -Verify 1 -naccept 1 2>>/tmp/backend-tls.log
done
