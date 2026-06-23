#!/usr/bin/env bash
# check_identity.sh — prove workload identity is issued on attestation, denied without it.
#
# Asserts:
#   1. backend gets exactly spiffe://meridian.local/backend
#   2. client  gets exactly spiffe://meridian.local/client
#   3. rogue (no registration entry) is REFUSED an SVID
#
# Run from the lab dir after `make up`:  bash check_identity.sh
set -uo pipefail

SOCK="/run/spire/sockets/agent.sock"
pass=0; fail=0
ok()   { echo "  PASS  $1"; pass=$((pass+1)); }
bad()  { echo "  FAIL  $1"; fail=$((fail+1)); }

fetch_id() { # $1 = service name
  docker compose exec -T "$1" spire-agent api fetch x509 -socketPath "$SOCK" 2>/dev/null \
    | sed -n 's/.*SPIFFE ID:[[:space:]]*//p' | head -n1
}

echo "== Registered workloads must receive the right identity =="
for svc in backend client; do
  id="$(fetch_id "$svc")"
  if [ "$id" = "spiffe://meridian.local/${svc}" ]; then
    ok "${svc} -> ${id}"
  else
    bad "${svc} expected spiffe://meridian.local/${svc}, got '${id:-<none>}'"
  fi
done

echo "== Unregistered workload must be DENIED an identity =="
docker compose --profile deny up -d rogue >/dev/null 2>&1
sleep 2
rid="$(docker compose exec -T rogue spire-agent api fetch x509 -socketPath "$SOCK" 2>&1 | sed -n 's/.*SPIFFE ID:[[:space:]]*//p' | head -n1)"
if [ -z "$rid" ]; then
  ok "rogue received no SVID (Workload API refused it)"
else
  bad "rogue should have no identity but got '${rid}'"
fi

echo ""
echo "== ${pass} passed, ${fail} failed =="
[ "$fail" -eq 0 ]
