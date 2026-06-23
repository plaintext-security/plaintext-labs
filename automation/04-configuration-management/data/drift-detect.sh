#!/usr/bin/env bash
# drift-detect.sh — declared-vs-observed drift detector for the hardening baseline.
#
# Detect-only by default: runs the playbook in check mode (a dry run), reports any
# host that has drifted off the declared state, and exits non-zero on drift so a
# scheduler/CI can alert. Pass --reconcile to self-heal: on detected drift, re-run
# enforcing and re-check (the detect-only-vs-auto-reconcile posture switch).
#
# Reference implementation. In the lab YOU author this and review every line — the
# parsing is fiddly and must (a) not flag an expected re-harden, (b) fail closed if
# the playbook itself errors.
set -uo pipefail

# PLAYBOOK defaults to the role YOU complete; the lab env validates this script
# against the reference role via PLAYBOOK=data/hardening-ref.yml.
PLAY="ansible-playbook -i data/inventory.ini ${PLAYBOOK:-data/hardening.yml}"
RECONCILE=0
[ "${1:-}" = "--reconcile" ] && RECONCILE=1

run_check() {
  # Dry run: detect, don't change. --diff prints the before/after of any drift.
  local out
  out="$($PLAY --check --diff 2>&1)"
  local rc=$?
  echo "$out"
  # Fail closed: a non-zero ansible exit that ISN'T just "changed" is a real error.
  if [ $rc -ne 0 ] && ! echo "$out" | grep -q 'changed=[0-9]'; then
    echo "ERROR: playbook failed to run (rc=$rc) — failing closed." >&2
    return 2
  fi
  # Drift = any host recap with changed=1 or more in check mode.
  if echo "$out" | grep -qE 'changed=[1-9]'; then
    return 1   # drift detected
  fi
  return 0     # steady-state
}

echo "=== drift-detect: checking declared vs observed state ==="
if run_check; then
  echo "RESULT: steady-state — host is on-spec (0 changed)."
  exit 0
fi
rc=$?
if [ $rc -eq 2 ]; then exit 2; fi

echo "RESULT: DRIFT DETECTED — host has wandered off the declared baseline (see --diff above)."
if [ "$RECONCILE" -eq 1 ]; then
  echo "=== --reconcile: re-enforcing the baseline ==="
  $PLAY --diff || { echo "ERROR: reconcile run failed." >&2; exit 2; }
  echo "=== re-checking steady-state ==="
  if run_check; then
    echo "RESULT: reconciled — back to steady-state."
    exit 0
  fi
  echo "RESULT: still drifted after reconcile — investigate." >&2
  exit 1
fi
echo "(detect-only: a human must reconcile. Re-run with --reconcile to self-heal.)"
exit 1
