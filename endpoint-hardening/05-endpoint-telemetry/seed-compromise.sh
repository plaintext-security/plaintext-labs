#!/usr/bin/env bash
# Detonate a REAL, documented persistence technique inside the lab container so
# osquery telemetry has something genuine to surface. This follows the Atomic
# Red Team T1053.003 (Scheduled Task/Job: Cron) pattern that data/atomic/
# stages: a script under /tmp invoked from a crontab entry. The osquery hunt
# in the lab then finds it via the cron_tabs and processes tables.
#
# Runs INSIDE the container (make seed). Authorization: this only acts on the
# disposable lab container you own.
set -euo pipefail

# Atomic Red Team T1053.003 "Cron - Replace crontab with referenced file" /
# "Add script to all cron sub-folders" style artifact: a tmp payload + a cron entry.
PAYLOAD="/tmp/art-cron-persist.sh"
cat > "$PAYLOAD" <<'EOF'
#!/bin/sh
# Simulated beacon — Atomic Red Team T1053.003 reference payload (benign).
while true; do
  # connect-out attempt so process_open_sockets has a row to find
  exec 3<>/dev/tcp/127.0.0.1/9 2>/dev/null || true
  sleep 60
done
EOF
chmod +x "$PAYLOAD"

# Install the cron persistence (cron_tabs table will surface this).
echo "* * * * * root $PAYLOAD" > /etc/cron.d/art-persistence
chmod 0644 /etc/cron.d/art-persistence
service cron start >/dev/null 2>&1 || cron || true

# Launch the payload now so the processes table shows a process running from /tmp.
nohup "$PAYLOAD" >/dev/null 2>&1 &

echo "Detonated T1053.003 cron-persistence artifact (Atomic Red Team pattern):"
echo "  payload : $PAYLOAD  (process running from /tmp -> osquery 'processes')"
echo "  cron    : /etc/cron.d/art-persistence  (osquery 'cron_tabs')"
echo "Now hunt it with osquery — see lab.md."
