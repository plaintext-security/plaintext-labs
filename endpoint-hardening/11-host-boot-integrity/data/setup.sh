#!/usr/bin/env bash
# setup.sh — build the known-good AIDE baseline for the watched tree.
#
# This is the "I just provisioned this host and trust its state" moment. Everything
# AIDE later flags is measured against the snapshot taken here. In the real world you
# run this on a clean, freshly-built host *before* it ever faces the network, and you
# move the resulting DB somewhere the host can't rewrite (read-only/offline media).
set -euo pipefail

CONF=/lab/data/aide.conf
DB=/var/lib/aide/aide.db

mkdir -p /var/lib/aide

echo "==> Building AIDE baseline from a clean, trusted filesystem state..."
echo "    config: $CONF"
echo "    watching: /srv/app, /etc/cron.d"
echo

# --init scans every watched path and writes the new database to database_out.
aide --config="$CONF" --init

# Promote the freshly-built DB to the active baseline AIDE will compare against.
mv -f /var/lib/aide/aide.db.new "$DB"

echo
echo "==> Baseline written: $DB"
echo "    $(wc -l < "$DB" 2>/dev/null || echo '?') lines; $(stat -c '%s bytes' "$DB" 2>/dev/null || echo '? bytes')"
echo
echo "This DB is now the trust anchor. Protect it: in production it belongs on"
echo "read-only/offline media so an attacker who lands on the host cannot rewrite it"
echo "to hide their changes. (See lab.md — that is the real control here.)"
