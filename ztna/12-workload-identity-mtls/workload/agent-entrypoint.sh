#!/usr/bin/env bash
# SPIRE agent entrypoint: wait for the bootstrap step to drop the join token,
# then start the agent with it. The agent then attests the node to the server
# and begins serving the Workload API on /run/spire/sockets/agent.sock.
set -euo pipefail

TOKEN_FILE="/opt/spire/shared/agent-join-token"
echo "[agent] waiting for join token at ${TOKEN_FILE} ..."
until [ -s "$TOKEN_FILE" ]; do sleep 1; done
TOKEN="$(cat "$TOKEN_FILE")"
echo "[agent] join token received; starting agent."

exec spire-agent run \
  -config /opt/spire/conf/agent/agent.conf \
  -joinToken "$TOKEN"
