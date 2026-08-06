#!/usr/bin/env bash
# operate.sh — act as a given identity/profile from the client container (the
# stand-in for an operator's laptop). The first argument is a LABEL, not
# necessarily a Teleport username: it selects both the identity file written
# by mint-cert.sh (<label>-identity.pem) and a private TELEPORT_HOME, so
# alice, mallory, and alice's short-lived expiry-test cert ("alice-short",
# still the real alice user underneath) all get separate profiles that never
# collide in one container.
#
# Usage: operate.sh <label> <login|status|ssh|recordings|play-latest|play ID>
set -uo pipefail

USER_NAME="${1:?usage: operate.sh <label> <action> [args...]}"; shift
ACTION="${1:?usage: operate.sh <label> <action> [args...]}"; shift || true

export TELEPORT_HOME="/root/.tsh-${USER_NAME}"
mkdir -p "$TELEPORT_HOME"
IDFILE="/opt/teleport/shared/${USER_NAME}-identity.pem"
PROXY="teleport-auth:3080"
NODE="app-prod-01"

case "$ACTION" in
  login)
    tsh login --proxy="$PROXY" --identity="$IDFILE" --insecure
    ;;
  status)
    tsh status
    ;;
  ssh)
    # "$@" is passed as ONE remote command string (e.g. "whoami; hostname"),
    # same as plain `ssh host 'cmd1; cmd2'` — the remote shell interprets it.
    tsh ssh "ubuntu@${NODE}" -- "$@"
    ;;
  recordings)
    tsh recordings ls
    ;;
  play-latest)
    # Best-effort: pull the most recent session id from JSON output. The
    # exact field name / table layout of `tsh recordings ls` has shifted
    # across Teleport releases — if this doesn't find one, run
    # `tsh recordings ls` yourself and `tsh play <id>` directly; that manual
    # path is always the source of truth for this step.
    sid="$(tsh recordings ls --format=json 2>/dev/null \
      | jq -r '(.[0].id // .[0].ID // .[0].sid // .[0].session_id // empty)' 2>/dev/null || true)"
    if [ -z "$sid" ]; then
      sid="$(tsh recordings ls 2>/dev/null | awk 'NR==2{print $1}')"
    fi
    if [ -z "$sid" ]; then
      echo "[operate] no recordings found yet — run 'tsh recordings ls' by hand." >&2
      exit 1
    fi
    echo "[operate] playing session ${sid} ..."
    tsh play "$sid"
    ;;
  play)
    tsh play "${1:?usage: operate.sh <user> play <session-id>}"
    ;;
  *)
    echo "[operate] unknown action: ${ACTION}" >&2
    exit 2
    ;;
esac
