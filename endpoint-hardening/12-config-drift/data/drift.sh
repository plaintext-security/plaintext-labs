#!/usr/bin/env bash
# Module 12 — Drift injection: the world acting on the host.
# Injects three realistic drifts, each violating ONE named control:
#   1. A (simulated) package post-install flips net.ipv4.conf.all.rp_filter 1->0  [CIS-3.3.7]
#   2. An operator re-opens root SSH: PermitRootLogin no->yes                       [CIS-5.2.10]
#   3. A deploy drops a world-writable file under /srv/meridian                     [CIS-6.1.10]
# Idempotent and re-runnable. `drift.sh undo` (or `make reset`) returns to baseline.
set -euo pipefail

action="${1:-inject}"

inject() {
  echo "== Injecting drift (the world acting on the host) =="

  # Drift 1 — package post-install hook flips a sysctl default back to 0.
  echo "  [1/3] package post-install: net.ipv4.conf.all.rp_filter 1 -> 0 (CIS-3.3.7)"
  sysctl -w net.ipv4.conf.all.rp_filter=0 >/dev/null 2>&1 || true
  # also rewrite the on-disk value so --check sees pending re-convergence
  if grep -q 'net.ipv4.conf.all.rp_filter' /etc/sysctl.d/99-meridian-hardening.conf 2>/dev/null; then
    sed -i 's/^net.ipv4.conf.all.rp_filter.*/net.ipv4.conf.all.rp_filter = 0/' \
      /etc/sysctl.d/99-meridian-hardening.conf
  fi

  # Drift 2 — operator re-opens root SSH at 2 a.m. and never reverts.
  echo "  [2/3] operator at 2am: PermitRootLogin no -> yes (CIS-5.2.10)"
  sed -i 's/^PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config

  # Drift 3 — a deploy leaves a world-writable file.
  echo "  [3/3] deploy drop: world-writable /srv/meridian/upload.tmp (CIS-6.1.10)"
  mkdir -p /srv/meridian
  echo "transient deploy artifact" > /srv/meridian/upload.tmp
  chmod 0666 /srv/meridian/upload.tmp

  echo "== Drift injected. The host still runs fine — that's why drift is invisible. =="
}

undo() {
  echo "== Reverting drift to clean baseline =="
  sysctl -w net.ipv4.conf.all.rp_filter=1 >/dev/null 2>&1 || true
  if grep -q 'net.ipv4.conf.all.rp_filter' /etc/sysctl.d/99-meridian-hardening.conf 2>/dev/null; then
    sed -i 's/^net.ipv4.conf.all.rp_filter.*/net.ipv4.conf.all.rp_filter = 1/' \
      /etc/sysctl.d/99-meridian-hardening.conf
  fi
  sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
  rm -f /srv/meridian/upload.tmp
  echo "== Reverted. =="
}

case "$action" in
  inject) inject ;;
  undo)   undo ;;
  *) echo "usage: drift.sh [inject|undo]"; exit 2 ;;
esac
