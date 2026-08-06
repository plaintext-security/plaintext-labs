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

# Teleport launches the session shell as the requested OS user, so `ubuntu`
# (the login in alice's role) must actually exist on this node — otherwise the
# SSH auth/RBAC path succeeds and only the final shell launch fails with
# "unknown user ubuntu". root already exists.
id -u ubuntu >/dev/null 2>&1 || useradd -m -s /bin/bash ubuntu

echo "[node] join token received; starting ssh_service (dialing out to the proxy)."

# --insecure: the node dials the proxy's self-signed web cert to join (the same
# cert clients skip with `tsh --insecure`); without it the join fails with
# "x509: certificate signed by unknown authority". Never use against a real
# cluster — pin the CA (teleport.ca_pin) instead.
exec teleport start \
  --config=/etc/teleport/node.yaml \
  --token="$TOKEN" \
  --insecure
