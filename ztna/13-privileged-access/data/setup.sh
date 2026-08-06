#!/usr/bin/env bash
# Bootstrap: runs once after the auth+proxy service is healthy.
#   1. Generate a one-hour node join token, written to the shared volume.
#   2. Create the two RBAC roles the lab uses:
#        - privileged-ops (alice)     — DELIBERATELY over-broad: root login,
#          every node in the fleet. Tightening this is the lab's Step 5.
#        - help-desk-staging (mallory) — a REAL role, correctly scoped to
#          staging hosts that don't exist here, so it correctly does NOT
#          match app-prod-01 (env=production).
#   3. Create the two local users. `tctl users add` leaves each user PENDING
#      a password/web-signup — that's fine, and deliberate: this lab never
#      completes that browser flow. `tctl auth sign` (Step 2 of the lab)
#      issues short-lived certs straight from the CA for a user regardless of
#      signup status, which is what keeps the whole flow scriptable.
set -euo pipefail

SHARED=/opt/teleport/shared
mkdir -p "$SHARED"

echo "==> Generating a node join token"
TOKEN="$(tctl tokens add --type=node --ttl=1h --format=text | tail -n1 | tr -d '[:space:]')"
if [ -z "$TOKEN" ]; then
  echo "!! failed to generate a join token" >&2
  exit 1
fi
printf '%s' "$TOKEN" > "${SHARED}/join-token"
echo "==> Join token written for the node."

echo "==> Creating roles (privileged-ops is deliberately over-broad — see Step 5)"
tctl create -f /opt/teleport/data/role-privileged-ops.yaml
tctl create -f /opt/teleport/data/role-help-desk-staging.yaml

echo "==> Creating users"
tctl users add alice   --roles=privileged-ops    --logins=ubuntu,root >/dev/null 2>&1 || true
tctl users add mallory --roles=help-desk-staging --logins=ubuntu      >/dev/null 2>&1 || true

echo "==> Roles now in the cluster:"
tctl get roles --format=text || true
echo "==> Bootstrap complete. (mint certs with: make login / make deny-role)"
