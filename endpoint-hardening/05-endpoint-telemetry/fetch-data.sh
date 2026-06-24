#!/usr/bin/env sh
# Stage a REAL attack artifact into the lab: the Atomic Red Team test for
# T1053.003 (Scheduled Task/Job: Cron) — Red Canary's open library of
# ATT&CK-mapped tests. We copy the actual test definition out of the shared
# cache so the learner's osquery telemetry surfaces a documented technique,
# not an invented compromise.
set -eu

# locate lib/fetch.sh by walking up to the labs root
. "$(d=$PWD; while [ ! -f "$d/lib/fetch.sh" ] && [ "$d" != / ]; do d=$(dirname "$d"); done; echo "$d")/lib/fetch.sh"

ART="$(fetch_repo atomic-red-team)"
mkdir -p data/atomic
# The real, upstream atomic test definition + docs for cron persistence.
cp "$ART/atomics/T1053.003/T1053.003.yaml" data/atomic/T1053.003.yaml
cp "$ART/atomics/T1053.003/T1053.003.md"   data/atomic/T1053.003.md

echo "Staged Atomic Red Team T1053.003 (cron persistence) into data/atomic/"
echo "This is the real technique your osquery hunt will surface once 'make seed' detonates it."
