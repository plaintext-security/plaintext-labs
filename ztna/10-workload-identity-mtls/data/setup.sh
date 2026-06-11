#!/usr/bin/env bash
# Bootstrap: runs once after the SPIRE server is healthy.
#   1. Generate a node join token (the agent's identity = spiffe://meridian.local/agent/node)
#   2. Create registration entries mapping Docker-label selectors -> SPIFFE IDs
#      for the two workloads we DO trust (backend, client).
#   3. Deliberately register NOTHING for "rogue" — that's the deny proof in the lab.
set -euo pipefail

SOCK="/tmp/spire-server/private/api.sock"
NODE_ID="spiffe://meridian.local/agent/node"
SHARED="/opt/spire/shared"
mkdir -p "$SHARED"

echo "==> Generating node join token (agent will attest as ${NODE_ID})"
TOKEN="$(spire-server token generate -socketPath "$SOCK" -spiffeID "$NODE_ID" \
  | sed -n 's/^Token: //p' | tr -d '[:space:]')"
if [ -z "$TOKEN" ]; then
  echo "!! failed to generate join token" >&2
  exit 1
fi
printf '%s' "$TOKEN" > "${SHARED}/agent-join-token"
echo "==> Join token written for the agent."

create_entry() {
  local name="$1"
  echo "==> Registering spiffe://meridian.local/${name}  (selector docker:label:com.meridian.svc:${name})"
  spire-server entry create -socketPath "$SOCK" \
    -parentID "$NODE_ID" \
    -spiffeID "spiffe://meridian.local/${name}" \
    -selector "docker:label:com.meridian.svc:${name}" \
    -x509SVIDTTL 300 || true
}

create_entry backend
create_entry client

echo "==> Registration entries:"
spire-server entry show -socketPath "$SOCK" || true
echo "==> Bootstrap complete. (No entry exists for 'rogue' — that's the deny test.)"
