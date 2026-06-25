#!/usr/bin/env bash
# Module 12 — the steady-state loop: detect -> diff -> (reconcile) -> alert.
#
# This is the wrapper the lab's "Automate & own it" step asks for. It runs the
# baseline playbook in --check --diff mode, parses the output into a CONTROL-NAMED
# delta (not a score), optionally reconciles, and emits a structured drift-event
# record. It FAILS CLOSED: if the check itself errors, that is a failure-to-verify,
# never a silent "no drift". It exits non-zero whenever drift was found so a
# cron/CI job can alarm.
#
# Usage:
#   drift-loop.sh detect       # detect + control-named diff only (no reconcile)
#   drift-loop.sh reconcile    # re-apply the baseline (auto-reconcile classes)
#   drift-loop.sh loop         # detect -> diff -> alert -> reconcile (the full beat)
set -uo pipefail

LAB=/lab
INV="/opt/inventory"
PLAYBOOK="$LAB/data/playbook.yml"
EVENTS="$LAB/drift-events.log"
mode="${1:-detect}"

# --- map a playbook task name to a stable control ID + a human label ----------
# The playbook task names already carry the control, e.g. "[CIS-5.2.10] Disable
# root SSH login". We extract the bracketed control and the value before->after
# from the --diff hunk where ansible shows it.
parse_delta() {
  # stdin: the raw ansible-playbook --check --diff output
  # stdout: one "control|task|before->after|path" line per changed control
  awk '
    /^TASK \[/ {
      # capture the task title; strip the leading "TASK [" and the trailing
      # "] ***...". Task names here begin with "[CIS-x.y.z] ...", so trim only
      # the outermost TASK brackets and the decorative stars.
      line=$0
      sub(/^TASK \[/, "", line)
      sub(/\] \*+[[:space:]]*$/, "", line)
      task=line
      # pull a CIS-x.y.z token out of the task title if present
      control="UNMAPPED"
      if (match(task, /CIS-[0-9.x]+/)) control=substr(task, RSTART, RLENGTH)
      before=""; after=""; path=""
      next
    }
    /^[+]/ && $0 !~ /^[+][+][+]/ { after = after (after==""?"":" ") substr($0,2) }
    /^-/  && $0 !~ /^---/        { before = before (before==""?"":" ") substr($0,2) }
    /^\+\+\+ / { path=$0; sub(/^\+\+\+ (after: )?/, "", path) }
    /^changed: \[/ {
      # a changed task on a --check run == pending re-convergence == drift
      printf("%s|%s|%s -> %s|%s\n", control, task, (before==""?"?":before), (after==""?"?":after), path)
    }
  '
}

run_check() {
  ANSIBLE_FORCE_COLOR=0 ansible-playbook -i "$INV" "$PLAYBOOK" --check --diff 2>&1
}

emit_event() {
  # control | before->after | action
  local control="$1" delta="$2" task="$3" action="$4"
  printf '{"ts":"%s","control":"%s","delta":"%s","task":"%s","action":"%s"}\n' \
    "$(date -u +%FT%TZ)" "$control" "$delta" "$task" "$action" | tee -a "$EVENTS"
}

detect() {
  local out rc
  out="$(run_check)"; rc=$?

  # FAIL CLOSED: a run we genuinely could not complete (an unreachable target,
  # a connection refusal, or a parser/playbook ERROR!) is failure-to-verify.
  # Match unreachable=[1-9] (NOT the benign unreachable=0 in every PLAY RECAP),
  # and deliberately skip task-level fatal/FAILED! lines that carry ignore_errors
  # /failed_when handlers — those are expected and reported as failed=0.
  if echo "$out" | grep -qiE 'unreachable=[1-9]|ERROR!|Connection.*refused|Failed to connect'; then
    echo "FATAL: drift check could not complete (controller could not verify the target)." >&2
    echo "       This is failure-to-verify, NOT 'no drift'. Exiting non-zero." >&2
    return 3
  fi

  local deltas
  deltas="$(echo "$out" | parse_delta)"

  if [ -z "$deltas" ]; then
    echo "OK: no drift. Observed == declared (clean host is silent)."
    return 0
  fi

  echo "DRIFT DETECTED — control-named delta (what changed, against which control):"
  echo "$deltas" | while IFS='|' read -r control task delta path; do
    printf '  %-12s %s   [%s]%s\n' "$control" "$delta" "$task" "${path:+  ($path)}"
  done
  # return 1 == drift found (so cron/CI alarms)
  return 1
}

reconcile() {
  echo "== Reconcile: re-applying the declared baseline =="
  ANSIBLE_FORCE_COLOR=0 ansible-playbook -i "$INV" "$PLAYBOOK" 2>&1 \
    | grep -E '(PLAY RECAP|ok=|changed=|failed=)'
}

loop() {
  echo "== Steady-state loop: detect -> diff -> alert -> reconcile =="
  local out rc
  out="$(run_check)"; rc=$?
  if echo "$out" | grep -qiE 'unreachable=[1-9]|ERROR!|Connection.*refused|Failed to connect'; then
    emit_event "ALL" "verify-failed" "drift-check" "FAIL-CLOSED"
    echo "FATAL: failure-to-verify; alerting and exiting non-zero." >&2
    return 3
  fi

  local deltas
  deltas="$(echo "$out" | parse_delta)"
  if [ -z "$deltas" ]; then
    echo "OK: clean host — no alert emitted (no false alarms)."
    return 0
  fi

  # ALERT FIRST, then reconcile — never auto-heal silently.
  echo "-- Alert: drift-event records (emitted BEFORE reconcile) --"
  echo "$deltas" | while IFS='|' read -r control task delta path; do
    emit_event "$control" "$delta" "$task" "auto-reconcile"
  done

  reconcile

  echo "-- Post-reconcile verify --"
  if detect; then
    echo "OK: steady-state restored (zero drift after reconcile)."
  else
    echo "WARNING: drift persists after reconcile — investigate (recurring cause?)." >&2
    return 1
  fi
}

case "$mode" in
  detect)    detect ;;
  reconcile) reconcile ;;
  loop)      loop ;;
  *) echo "usage: drift-loop.sh [detect|reconcile|loop]"; exit 2 ;;
esac
