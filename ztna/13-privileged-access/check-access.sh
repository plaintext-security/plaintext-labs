#!/usr/bin/env bash
# check-access.sh — regression test of the access control for Module 13
# (Teleport). Asserts:
#   1. alice (privileged-ops) CAN reach app-prod-01 as ubuntu — the control
#      anchor; if this fails, the other two assertions prove nothing.
#   2. mallory (help-desk-staging — a real role, wrong environment) is
#      DENIED by RBAC.
#   3. A direct connection to app-prod-01:3022, skipping the proxy entirely,
#      is REFUSED — the node has no listener to bypass into.
#
# Run from the lab dir after `make up`:  bash check-access.sh
set -uo pipefail

pass=0; fail=0
ok()  { echo "  PASS  $1"; pass=$((pass+1)); }
bad() { echo "  FAIL  $1"; fail=$((fail+1)); }

mint() { docker compose exec -T teleport-auth bash /opt/teleport/workload/mint-cert.sh "$1" "${2:-15m}" >/dev/null 2>&1; }
op()   { docker compose exec -T client bash /opt/teleport/workload/operate.sh "$@"; }

echo "== Authorized identity must be ALLOWED (control anchor) =="
mint alice 15m
op alice login >/dev/null 2>&1
out="$(op alice ssh whoami 2>&1)"; rc=$?
# strip the PTY's carriage returns before matching (the session is interactive
# so the recording is replayable — see operate.sh)
if [ "$rc" -eq 0 ] && echo "$out" | tr -d '\r' | grep -qx ubuntu; then
  ok "alice (privileged-ops) -> ubuntu@app-prod-01 succeeded"
else
  bad "alice should have reached app-prod-01 as ubuntu (rc=${rc}), got: ${out}"
fi

echo "== Unauthorized identity must be DENIED =="
mint mallory 15m
op mallory login >/dev/null 2>&1
out="$(op mallory ssh whoami 2>&1)"; rc=$?
if [ "$rc" -ne 0 ] && ! echo "$out" | tr -d '\r' | grep -qx ubuntu; then
  ok "mallory (help-desk-staging, env=staging) denied access to app-prod-01 (env=production)"
else
  bad "mallory should have been denied (rc=${rc}), got: ${out}"
fi

echo "== Direct-to-node bypass must be REFUSED =="
if docker compose exec -T client nc -z -w3 app-prod-01 3022 2>/dev/null; then
  bad "direct connection to app-prod-01:3022 succeeded — should be refused"
else
  ok "direct connection to app-prod-01:3022 refused (no listener — the node only dials out)"
fi

echo ""
echo "== ${pass} passed, ${fail} failed =="
[ "$fail" -eq 0 ]
