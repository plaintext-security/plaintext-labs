#!/bin/bash
# Server entrypoint: generate a self-signed RSA cert (gitignored, never
# committed), install the CLASSICAL-ONLY nginx config as the brownfield
# baseline, then run nginx in the foreground.
set -e

CERTDIR=/etc/nginx/certs
mkdir -p "$CERTDIR" /var/lib/nginx/logs /run/nginx

if [ ! -f "$CERTDIR/server.crt" ]; then
  echo "[entrypoint] generating self-signed RSA server certificate..."
  openssl req -x509 -nodes -newkey rsa:2048 \
    -keyout "$CERTDIR/server.key" \
    -out "$CERTDIR/server.crt" \
    -days 365 \
    -subj "/CN=pqc-server/O=Meridian/C=US" \
    -addext "subjectAltName=DNS:pqc-server,DNS:server,DNS:localhost" \
    2>/dev/null
  echo "[entrypoint] cert key type: RSA-2048 (the brownfield baseline)"
fi

# Install the classical-only config as the starting (pre-migration) state.
# `make migrate` swaps in nginx-hybrid.conf; `make rollback`/`make reset`
# restore this one. Re-running the entrypoint always resets to classical.
cp /lab/data/nginx-classical.conf /etc/nginx/http.d/default.conf

echo "[entrypoint] starting nginx with CLASSICAL ECDHE/RSA config (no PQC)..."
exec nginx -g 'daemon off;'
