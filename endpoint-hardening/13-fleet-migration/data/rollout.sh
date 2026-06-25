#!/usr/bin/env bash
# Module 13 — the staged rolling rollout.
# Applies the Module-06 baseline to a named ring with the rolling-upgrade
# pattern: health-check (before) -> apply in batches (serial) -> health-check
# (after) per batch, HALTING when a batch's failures cross max_fail_percentage.
# This is the script-driven equivalent of Ansible `serial` + `max_fail_percentage`
# + pre/post `health` hooks (see playbook.yml for the Ansible expression of the
# same pattern) — kept as a script so the demo is deterministic and CI-runnable.
#
#   rollout.sh roll  <ring> [SERIAL] [MAX_FAIL_PCT] [EXCEPTION]
#   rollout.sh back  <ring>          # per-ring rollback: re-converge to unhardened
#
#   EXCEPTION=1  -> the legacy host in the ring gets the relaxed profile (umask 022)
#                   instead of the full baseline (the defended exception).
set -uo pipefail

FLEET=/fleet
INV=/lab/data/inventory.ini
# Invoke via `bash` so it works even when the executable bit didn't survive
# git/Docker COPY (these scripts are committed mode 644).
HEALTH="bash /lab/fleet-health.sh"

ring="${2:-}"
SERIAL="${3:-2}"          # batch size for the fleet ring
MAX_FAIL_PCT="${4:-25}"   # halt when a batch's failure % crosses this
EXCEPTION="${5:-0}"

hosts_in_ring() {
  awk -v R="[$1]" '
    $0==R {f=1; next} /^\[/ {f=0}
    f && NF {gsub(/#.*/,""); if($1!="") print $1}
  ' "$INV"
}
is_legacy() { grep -E "^LEGACY=1" "$FLEET/$1/state.env" >/dev/null 2>&1; }

apply_full() { # set the host's state to the full baseline (breaks legacy on umask)
  local h="$1"
  sed -i 's/^PROFILE=.*/PROFILE=full-baseline/;
          s/^ROOT_SSH=.*/ROOT_SSH=no/;
          s/^UMASK=.*/UMASK=027/;
          s/^RP_FILTER=.*/RP_FILTER=1/;
          s/^MINLEN=.*/MINLEN=14/' "$FLEET/$h/state.env"
}
apply_relaxed() { # legacy exception: full baseline EXCEPT umask stays 022
  local h="$1"
  sed -i 's/^PROFILE=.*/PROFILE=relaxed-legacy/;
          s/^ROOT_SSH=.*/ROOT_SSH=no/;
          s/^UMASK=.*/UMASK=022/;
          s/^RP_FILTER=.*/RP_FILTER=1/;
          s/^MINLEN=.*/MINLEN=14/' "$FLEET/$h/state.env"
}
apply_unhardened() { # rollback target
  local h="$1"
  sed -i 's/^PROFILE=.*/PROFILE=unhardened/;
          s/^ROOT_SSH=.*/ROOT_SSH=yes/;
          s/^UMASK=.*/UMASK=022/;
          s/^RP_FILTER=.*/RP_FILTER=0/;
          s/^MINLEN=.*/MINLEN=8/' "$FLEET/$h/state.env"
}

roll() {
  local hosts; hosts=$(hosts_in_ring "$ring")
  [ -z "$hosts" ] && { echo "no hosts in ring '$ring'"; exit 2; }
  echo "=== ROLL ring='$ring' serial=$SERIAL max_fail=${MAX_FAIL_PCT}% exception=$EXCEPTION ==="

  echo "-- health BEFORE (every host in ring must be serving) --"
  if $HEALTH "$ring" no; then
    :
  elif [ "$EXCEPTION" = "1" ]; then
    # We are re-rolling specifically to REPAIR a host the full baseline broke
    # (apply the defended exception). A currently-broken legacy host is the
    # reason we're here, so don't hard-abort — proceed to converge it healthy.
    echo "-- (a host is down; re-rolling WITH the exception to repair it) --"
  else
    echo "ABORT: ring not healthy before roll."; exit 1
  fi

  # Batch the ring (serial). After each batch, run the AFTER health gate; if a
  # batch's failure % crosses MAX_FAIL_PCT, HALT — rest of fleet untouched.
  local total; total=$(echo "$hosts" | wc -w)
  local idx=0
  local batch=()
  for h in $hosts; do
    batch+=("$h")
    idx=$((idx+1))
    if [ "${#batch[@]}" -ge "$SERIAL" ] || [ "$idx" -eq "$total" ]; then
      echo "-- applying batch: ${batch[*]} --"
      for bh in "${batch[@]}"; do
        if is_legacy "$bh" && [ "$EXCEPTION" = "1" ]; then
          echo "   $bh: applying RELAXED exception profile (umask 022)"
          apply_relaxed "$bh"
        else
          echo "   $bh: applying full baseline"
          apply_full "$bh"
        fi
      done
      sleep 1
      echo "-- health AFTER batch (hardened AND still serving) --"
      if ! $HEALTH "$ring" yes; then
        # compute this batch's failure share to decide halt
        local fails=0
        for bh in "${batch[@]}"; do
          port=$(( 18000 + 10#${bh##*-} ))
          code=$(curl -s -o /dev/null -m 3 -w '%{http_code}' "http://127.0.0.1:$port/health" 2>/dev/null || echo 000)
          [ "$code" != "200" ] && fails=$((fails+1))
        done
        local pct=$(( fails * 100 / ${#batch[@]} ))
        echo "!! batch failure: ${fails}/${#batch[@]} (${pct}%) vs max_fail_percentage=${MAX_FAIL_PCT}%"
        if [ "$pct" -gt "$MAX_FAIL_PCT" ]; then
          echo "!! HALT: rollout stopped. The REST OF THE FLEET IS UNTOUCHED (no big-bang outage)."
          exit 1
        fi
      fi
      batch=()
    fi
  done
  echo "=== ring '$ring' rolled. ==="
}

back() {
  echo "=== ROLLBACK ring='$ring' -> previous (unhardened) state ==="
  for h in $(hosts_in_ring "$ring"); do
    echo "   $h: re-converging to previous state"
    apply_unhardened "$h"
  done
  sleep 1
  $HEALTH "$ring" no
  echo "=== ring '$ring' rolled back (serving the old way again). ==="
}

case "${1:-}" in
  roll) roll ;;
  back) back ;;
  *) echo "usage: rollout.sh [roll|back] <ring> [SERIAL] [MAX_FAIL_PCT] [EXCEPTION]"; exit 2 ;;
esac
