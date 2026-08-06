#!/usr/bin/env bash
# mint-cert.sh — admin-side certificate issuance. Run on the teleport-auth
# container (tctl needs local access to the CA / auth socket).
#
# `tctl auth sign` is the administrator's OFFLINE equivalent of `tsh login` —
# it signs a certificate straight from the cluster CA for an existing user,
# scoped to that user's roles, with an explicit TTL. No browser, no password
# reset. This is what keeps the lab fully scriptable; a real deployment puts
# a human through `tsh login` (SSO / WebAuthn / password) instead, and gets
# back a certificate of the identical shape.
#
# Usage: mint-cert.sh <user> [ttl] [label]
#   <user>  must be a real Teleport user (created in data/setup.sh).
#   [label] names the output identity file when you want more than one cert
#           for the SAME user without clobbering the other (e.g. the
#           deny-expired step mints alice a second, 30s-TTL cert under the
#           label "alice-short" so her normal 15m cert is untouched).
set -euo pipefail

USER_NAME="${1:?usage: mint-cert.sh <user> [ttl] [label]}"
TTL="${2:-15m}"
LABEL="${3:-$USER_NAME}"
OUT="/opt/teleport/shared/${LABEL}-identity.pem"

rm -f "$OUT"
echo "[auth] minting a ${TTL} certificate for ${USER_NAME} (label: ${LABEL}) ..."
tctl auth sign --user="$USER_NAME" --format=file --out="$OUT" --ttl="$TTL"
echo "[auth] wrote ${OUT}"
