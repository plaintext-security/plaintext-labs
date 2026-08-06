#!/usr/bin/env bash
# Node entrypoint: wait for the bootstrap step to drop the join token, then
# start ssh_service. The node JOINS by dialing OUT to the proxy
# (teleport.proxy_server in conf/node.yaml) — it never opens an inbound
# listener. That's what makes "connect directly, skip the proxy" refused
# rather than merely firewalled: there's nothing here to bypass into.
set -euo pipefail

TOKEN_FILE="/opt/teleport/shared/join-token"
echo "[node] waiting for join token at ${TOKEN_FILE} ..."
until [ -s "$TOKEN_FILE" ]; do sleep 1; done
TOKEN="$(cat "$TOKEN_FILE")"
echo "[node] join token received; starting ssh_service (dialing out to the proxy)."

exec teleport start \
  --config=/etc/teleport/node.yaml \
  --token="$TOKEN"
