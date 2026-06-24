#!/usr/bin/env bash
# drift-introduce.sh — introduce a MONTH OF DECAY on the Corp domain.
#
# TWO modes:
#   (default)  MUTATE the observed-posture seed (data/observed.json) — deterministic, CI-safe,
#              so `make detect` always has the same change to find.
#   --live     Run REAL `samba-tool` against the bundled DC (dc01.corp.local) to register a new
#              Kerberoastable SPN and add an unexpected member to Domain Admins, then let
#              `make detect-live` collect the drift over LDAP. This is the genuine-DC path; the
#              detector logic is identical, only the source of the facts changes.
#
# Mutations (each a realistic, independently-introduced regression):
#   1. New Kerberoastable SPN registered on svc-newdb           -> T1558.003
#   2. GenericWrite re-added on Finance-Managers (re-grown ACE)  -> T1098 / T1484.001  (seed mode only)
#   3. A user (mnguyen) added to Domain Admins (unexpected)      -> T1098
#   4. krbtgt clock advanced past the baseline threshold         -> standing T1558.001 (seed mode only)
#
# The learner is NOT told the exact set from the lab text — the detector must surface each item.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OBS="${HERE}/data/observed.json"
CLEAN="${HERE}/data/observed.clean.json"

# ---- LIVE mode: real samba-tool against the DC ---------------------------------------------
if [ "${1:-}" = "--live" ]; then
    DC_HOST="${DC_ADMIN_HOST:-dc01.corp.local}"
    ADMIN_PASS="${SAMBA_ADMIN_PASSWORD:-C0rp@Admin!}"
    echo "[*] LIVE drift: running real samba-tool against ${DC_HOST} (Administrator)..."
    # 1. Register a new Kerberoastable SPN on a freshly-created service account.
    samba-tool user create svc-newdb 'N3wDb$3rv1ce!' \
        -H "ldap://${DC_HOST}" -U "Administrator%${ADMIN_PASS}" 2>/dev/null || true
    samba-tool spn add "MSSQLSvc/newdb01.corp.local:1433" svc-newdb \
        -H "ldap://${DC_HOST}" -U "Administrator%${ADMIN_PASS}" 2>/dev/null || true
    # 3. Add an unexpected member to Domain Admins.
    samba-tool group addmembers "Domain Admins" mnguyen \
        -H "ldap://${DC_HOST}" -U "Administrator%${ADMIN_PASS}" 2>/dev/null || true
    echo "[*] Live drift introduced on ${DC_HOST}."
    echo "    Run 'make detect-live' (python3 drift-detect.py --live) to collect + name it over LDAP."
    echo "    (The ACE re-grow and krbtgt-age regressions are exercised in the deterministic seed mode.)"
    exit 0
fi

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
