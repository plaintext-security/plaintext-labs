#!/usr/bin/env sh
# Stage REAL Windows attack telemetry into the lab from the shared cache:
# three EVTX samples from sbousseaden/EVTX-ATTACK-SAMPLES (GPL-3.0), one per
# attack phase. These are genuine Windows/Sysmon event logs of real techniques —
# not an invented alert feed. fetch-data.sh copies the .evtx; the in-container
# `make convert` turns them into the flat JSON the Sigma matcher consumes.
set -eu

. "$(d=$PWD; while [ ! -f "$d/lib/fetch.sh" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/lib/fetch.sh"

EVTX="$(fetch_repo evtx-attack-samples)"
mkdir -p data/evtx

# One real sample per attack phase (exact upstream paths):
#   Persistence       -> Registry Run-key persistence (ATT&CK T1547.001)
#   Credential Access -> LSASS memory dump via mimikatz (ATT&CK T1003.001)
#   Lateral Movement  -> remote service install / PsExec (ATT&CK T1021.002 / T1543.003)
cp "$EVTX/Persistence/evasion_persis_hidden_run_keyvalue_sysmon_13.evtx" \
   data/evtx/persistence_runkey_T1547.001.evtx
cp "$EVTX/Credential Access/sysmon_10_lsass_mimikatz_sekurlsa_logonpasswords.evtx" \
   data/evtx/credaccess_lsass_T1003.001.evtx
cp "$EVTX/Lateral Movement/LM_Remote_Service02_7045.evtx" \
   data/evtx/lateral_remote_service_T1021.002.evtx

echo "Staged 3 real EVTX-ATTACK-SAMPLES into data/evtx/ (persistence / cred-access / lateral)."
echo "Run 'make convert' (or 'make up') to render them to data/events.json for Sigma matching."
