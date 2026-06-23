#!/usr/bin/env bash
# drift-introduce.sh — simulate a MONTH OF DECAY on the hardened Meridian domain.
#
# In a full Samba-DC build this would run real `samba-tool spn add`, `dacledit.py`,
# `samba-tool group addmembers`, and advance the krbtgt clock against the live dc01. In this
# deterministic SIMULATION it instead MUTATES the observed-posture seed (data/observed.json)
# with the same NET EFFECT, so drift-detect.py has real change to find. The learner is NOT
# told the exact set from the lab text — the detector must surface each item.
#
# Mutations applied (each is a realistic, independently-introduced regression):
#   1. New Kerberoastable SPN registered on svc-newdb        -> T1558.003
#   2. GenericWrite re-added on Finance-Managers (re-grown ACE) -> T1098 / T1484.001
#   3. A user (mnguyen) added to Domain Admins (unexpected)   -> T1098
#   4. krbtgt clock advanced past the baseline threshold      -> standing T1558.001
#
# Reproducible: resets observed.json from observed.clean.json first, then applies the set.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OBS="${HERE}/data/observed.json"
CLEAN="${HERE}/data/observed.clean.json"

echo "[*] Resetting observed posture to the clean hardened state..."
cp "${CLEAN}" "${OBS}"

echo "[*] Applying a simulated month of drift to ${OBS}..."
python3 - "$OBS" <<'PY'
import json, sys
path = sys.argv[1]
with open(path) as f:
    o = json.load(f)

# 1. New Kerberoastable service account (someone stood up a DB service the old way).
if "svc-newdb" not in o["kerberoastable_accounts"]:
    o["kerberoastable_accounts"].append("svc-newdb")

# 2. Dangerous ACE re-added on a privileged-adjacent object.
ace = {"principal": "svc-deploy", "right": "GenericWrite", "on_object": "Finance-Managers"}
if ace not in o["dangerous_aces"]:
    o["dangerous_aces"].append(ace)

# 3. Unexpected member added to Domain Admins.
da = o["privileged_group_rosters"]["Domain Admins"]
if "mnguyen" not in da:
    da.append("mnguyen")

# 4. krbtgt aged past the baseline threshold (180d): advance the simulated clock.
o["krbtgt"]["age_days"] = 211

with open(path, "w") as f:
    json.dump(o, f, indent=2)
    f.write("\n")
PY

echo "[*] Drift introduced. The observed posture now diverges from data/baseline.json."
echo "    Re-run the detector ('make detect' or python3 drift-detect.py) to find every change."
