#!/usr/bin/env bash
# Module 13 — the in-service fleet model.
# Models ~6 hosts as state dirs under /fleet/<host>/, each running a tiny HTTP
# health endpoint (the host is doing a job, not an empty box). The health server
# returns 200 when the host's app is serving, and 503 when a control has broken
# it (the legacy host under the full baseline).
#
#   fleet.sh init     # create the fleet, start every host's app, all serving 200, unhardened
#   fleet.sh stop     # stop all host apps
#   fleet.sh port HOST   # print the host's health port
set -euo pipefail

FLEET=/fleet
HOSTS="host-01 host-02 host-03 host-04 host-05 host-06"
LEGACY="host-05"
BASE_PORT=18000

port_for() {
  # deterministic port per host: host-01 -> 18001 ...
  local n="${1##*-}"; echo $(( BASE_PORT + 10#$n ))
}

# The per-host app. Health logic, in Python so it's robust:
#   - reads /fleet/<host>/state.env  (PROFILE, UMASK, ROOT_SSH, RP_FILTER, ...)
#   - LEGACY app requires UMASK=022. If UMASK=027 AND this host is legacy AND it
#     is NOT on the relaxed exception profile -> the app is BROKEN -> 503.
#   - every other host serves 200 regardless of hardening.
write_app() {
  cat > "$FLEET/app.py" <<'PY'
import os, sys
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = sys.argv[1]
PORT = int(sys.argv[2])
STATE = f"/fleet/{HOST}/state.env"

def read_state():
    s = {}
    try:
        with open(STATE) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    s[k] = v
    except FileNotFoundError:
        pass
    return s

class H(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass
    def do_GET(self):
        s = read_state()
        is_legacy = s.get("LEGACY", "0") == "1"
        umask = s.get("UMASK", "022")
        profile = s.get("PROFILE", "unhardened")
        # The legacy vendor app requires a loose umask; the full baseline (027)
        # breaks it. The relaxed exception profile (relaxed-legacy) keeps umask=022,
        # so it never trips this. The umask check is what actually breaks the app;
        # the profile guard makes the intent explicit.
        broken = is_legacy and umask == "027" and profile != "relaxed-legacy"
        if self.path != "/health":
            self.send_response(404); self.end_headers(); return
        if broken:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b'{"status":"DOWN","reason":"legacy app requires umask=022; baseline set 027"}')
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(f'{{"status":"UP","profile":"{profile}"}}'.encode())

HTTPServer(("127.0.0.1", PORT), H).serve_forever()
PY
}

init() {
  mkdir -p "$FLEET"
  write_app
  for h in $HOSTS; do
    mkdir -p "$FLEET/$h"
    local legacy=0; [ "$h" = "$LEGACY" ] && legacy=1
    # all hosts start UNHARDENED but SERVING
    cat > "$FLEET/$h/state.env" <<EOF
HOST=$h
LEGACY=$legacy
PROFILE=unhardened
ROOT_SSH=yes
UMASK=022
RP_FILTER=0
MINLEN=8
EOF
    local p; p=$(port_for "$h")
    # (re)start the app
    [ -f "$FLEET/$h/app.pid" ] && kill "$(cat "$FLEET/$h/app.pid")" 2>/dev/null || true
    nohup python3 "$FLEET/app.py" "$h" "$p" >/dev/null 2>&1 &
    echo $! > "$FLEET/$h/app.pid"
  done
  sleep 1
  echo "Fleet up: $HOSTS (each serving /health, all unhardened)"
}

stop() {
  for h in $HOSTS; do
    [ -f "$FLEET/$h/app.pid" ] && kill "$(cat "$FLEET/$h/app.pid")" 2>/dev/null || true
  done
  echo "Fleet stopped."
}

case "${1:-init}" in
  init) init ;;
  stop) stop ;;
  port) port_for "$2" ;;
  *) echo "usage: fleet.sh [init|stop|port HOST]"; exit 2 ;;
esac
