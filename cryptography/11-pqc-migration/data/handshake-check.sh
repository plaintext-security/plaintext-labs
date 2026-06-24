#!/bin/bash
# handshake-check.sh <host[:port]> — the before/after migration gate.
#
# This is the success signal for the lab and the `make verify` / `make demo`
# equivalent. It runs INSIDE the client containers (the modern OpenSSL-3.5
# client and the legacy OpenSSL-3.1 client) and asserts the migration held:
#
#   1. MODERN client negotiates the HYBRID group exactly (X25519MLKEM768) —
#      parsed from s_client output, string-matched. A successful handshake that
#      SILENTLY fell back to classical X25519 is a FAILURE, not a pass — that is
#      the exact bug this lab teaches.
#   2. LEGACY client still completes a CLASSICAL handshake (the fallback works).
#   3. Both clients get an HTTP 200 through the migrated TLS.
#
# FAIL CLOSED: a connection error, a timeout, or an s_client that could not run
# counts as a FAILURE. Exits non-zero on any failed assertion.
#
# It is meant to FAIL before `make migrate` (modern client on classical) and
# PASS after. It runs each role against the appropriate client container; when
# invoked with no role it expects $ROLE in {modern,legacy} (set by the Makefile).
set -u

HOST="${1:-server:443}"
ROLE="${ROLE:-modern}"
TIMEOUT="${TIMEOUT:-10}"

fail() { echo "[FAIL] $1"; exit 1; }
ok()   { echo "[ OK ] $1"; }

# Run an s_client handshake and capture output (stderr+stdout). Returns the
# captured text; sets RC to the openssl exit code.
do_handshake() {
  local groups_flag="$1"
  echo "Q" | timeout "$TIMEOUT" openssl s_client -connect "$HOST" -tls1_3 $groups_flag 2>&1
}

# Extract the negotiated TLS 1.3 group. OpenSSL 3.5 prints
# "Negotiated TLS1.3 group: X25519MLKEM768"; older builds print it too for
# classical groups. Fall back to the "Server Temp Key" line if needed.
parse_group() {
  local out="$1"
  local g
  g=$(printf '%s\n' "$out" | grep -i "Negotiated TLS1.3 group:" | head -1 | sed -E 's/.*group:[[:space:]]*//I' | tr -d '\r')
  if [ -z "$g" ]; then
    g=$(printf '%s\n' "$out" | grep -i "Server Temp Key:" | head -1 | sed -E 's/.*Key:[[:space:]]*//I' | tr -d '\r')
  fi
  printf '%s' "$g"
}

check_request() {
  local code
  code=$(timeout "$TIMEOUT" curl -sk -o /dev/null -w '%{http_code}' "https://${HOST%%:*}:${HOST##*:}/" 2>/dev/null)
  [ "$code" = "200" ] || fail "$ROLE: request did not return 200 (got '${code:-<none>}')"
  ok "$ROLE: request returned HTTP 200 through migrated TLS"
}

case "$ROLE" in
  modern)
    echo "== MODERN client: assert HYBRID negotiation =="
    OUT=$(do_handshake "-groups X25519MLKEM768:X25519")
    RC=$?
    [ $RC -eq 0 ] || fail "modern: s_client handshake failed/timed out (rc=$RC) — fail closed"
    GROUP=$(parse_group "$OUT")
    echo "    negotiated group: ${GROUP:-<unparsed>}"
    # String-match the HYBRID group. A classical X25519 here = silent fallback = FAILURE.
    case "$GROUP" in
      *X25519MLKEM768*) ok "modern: negotiated HYBRID X25519MLKEM768 (quantum-safe path)";;
      "")               fail "modern: could not parse negotiated group — fail closed";;
      *)                fail "modern: negotiated '$GROUP' (classical) — migration did NOT take / silent fallback";;
    esac
    check_request
    ;;
  legacy)
    echo "== LEGACY client: assert interop preserved (classical) =="
    OUT=$(do_handshake "")
    RC=$?
    [ $RC -eq 0 ] || fail "legacy: s_client handshake failed/timed out (rc=$RC) — interop broken"
    GROUP=$(parse_group "$OUT")
    echo "    negotiated group: ${GROUP:-<unparsed>}"
    case "$GROUP" in
      *MLKEM*) fail "legacy: unexpectedly negotiated a PQC group '$GROUP' (this client should be classical-only)";;
      "")      fail "legacy: handshake produced no group — interop broken, fail closed";;
      *)       ok "legacy: still negotiates classical '$GROUP' — interop preserved";;
    esac
    check_request
    ;;
  *)
    fail "unknown ROLE='$ROLE' (expected modern|legacy)"
    ;;
esac

echo "[PASS] $ROLE checks passed"
