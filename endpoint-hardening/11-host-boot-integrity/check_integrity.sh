#!/usr/bin/env bash
# check_integrity.sh — prove the AIDE baseline behaves correctly:
#
#   --baseline-clean : right after `make up` (no tamper), AIDE reports NO changes.
#   --detects        : after `make tamper`, AIDE flags all three planted changes
#                      (modified binary, new SUID-root file, dropped cron job).
#
# Default (no arg) runs whichever assertion fits the current state by inspecting
# the report, so `make check` works before OR after a tamper.
#
# Run inside the host container (the Makefile does this for you):
#   docker compose exec -T host bash check_integrity.sh [--baseline-clean|--detects]
set -uo pipefail

CONF=/lab/data/aide.conf
pass=0; fail=0
ok()  { echo "  PASS  $1"; pass=$((pass+1)); }
bad() { echo "  FAIL  $1"; fail=$((fail+1)); }

# AIDE --check exits 0 when clean, non-zero (a bitfield) when it finds differences.
# We capture both the report text and the exit code; we key assertions on the text
# so we don't depend on the exact bit values across AIDE versions.
run_check() {
  aide --config="$CONF" --check 2>&1
}

REPORT="$(run_check)"; RC=$?

# Heuristic: AIDE prints "found differences" / a summary with non-zero counts when
# anything changed. Treat a clean run as: exit 0 AND none of our planted paths named.
planted_seen=0
echo "$REPORT" | grep -q '/srv/app/bin/meridian'        && planted_seen=1
echo "$REPORT" | grep -q '/srv/app/bin/\.helper'        && planted_seen=1
echo "$REPORT" | grep -q '/etc/cron\.d/meridian-update' && planted_seen=1

MODE="${1:-auto}"
if [ "$MODE" = "auto" ]; then
  if [ "$RC" -eq 0 ] && [ "$planted_seen" -eq 0 ]; then MODE="--baseline-clean"; else MODE="--detects"; fi
  echo "== auto-detected mode: $MODE =="
fi

case "$MODE" in
  --baseline-clean)
    echo "== Baseline must be CLEAN before any tamper =="
    if [ "$RC" -eq 0 ]; then
      ok "AIDE --check reports no differences (exit 0)"
    else
      bad "AIDE reported changes against a fresh baseline (exit $RC) — re-run 'make reset && make up'"
    fi
    if [ "$planted_seen" -eq 0 ]; then
      ok "no planted paths present in the report"
    else
      bad "a planted path is already present — did you run 'make tamper' before checking clean?"
    fi
    ;;

  --detects)
    echo "== After tamper, AIDE must flag all three planted changes =="
    if [ "$RC" -ne 0 ]; then
      ok "AIDE --check signalled differences (non-zero exit $RC)"
    else
      bad "AIDE returned 0 (clean) but a tamper was expected — was 'make tamper' run? is the DB current?"
    fi
    if echo "$REPORT" | grep -q '/srv/app/bin/meridian'; then
      ok "modified binary detected: /srv/app/bin/meridian"
    else
      bad "modified binary NOT detected: /srv/app/bin/meridian"
    fi
    if echo "$REPORT" | grep -q '/srv/app/bin/\.helper'; then
      ok "new SUID-root file detected: /srv/app/bin/.helper"
    else
      bad "new SUID-root file NOT detected: /srv/app/bin/.helper"
    fi
    if echo "$REPORT" | grep -q '/etc/cron\.d/meridian-update'; then
      ok "dropped cron job detected: /etc/cron.d/meridian-update"
    else
      bad "dropped cron job NOT detected: /etc/cron.d/meridian-update"
    fi
    ;;

  *)
    echo "usage: $0 [--baseline-clean|--detects]"; exit 2;;
esac

echo ""
echo "----- AIDE report (excerpt) -----------------------------------------"
echo "$REPORT" | sed -n '1,40p'
echo "---------------------------------------------------------------------"
echo ""
echo "== ${pass} passed, ${fail} failed =="
[ "$fail" -eq 0 ]
