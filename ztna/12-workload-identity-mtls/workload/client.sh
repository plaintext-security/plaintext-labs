#!/usr/bin/env bash
# client workload: stays alive so the demo / lab steps can exec into it and run
# the mTLS connection to the backend on demand. The fetch+connect logic lives in
# connect.sh so it can be re-run by hand.
set -uo pipefail
echo "[client] ready. Use: docker compose exec client /opt/spire/workload/connect.sh"
exec sleep infinity
