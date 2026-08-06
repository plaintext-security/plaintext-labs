#!/usr/bin/env bash
# data/scan.sh — run Prowler against the seeded floci account and print the
# HIGH/CRITICAL failures. Kept as a script (not inlined in the Makefile) so the
# jq program isn't mangled by nested Make/shell quoting.
#
# Prowler reads the emulator endpoint from AWS_ENDPOINT_URL (set in
# docker-compose.yml); the build-time patch in patch-prowler-endpoint.py makes
# its STS credential check honour that endpoint too. Scoped to the four services
# the lab seeds so the scan finishes in well under a minute.
set -uo pipefail

OUT_DIR=/tmp/prowler-out
OUT_NAME=prowler-demo
OCSF="$OUT_DIR/${OUT_NAME}.ocsf.json"

echo "== Running prowler posture scan against floci (s3, ec2, iam, cloudtrail) =="
# Prowler exits non-zero when it finds failing checks — that's success for us.
prowler aws \
  --services s3 ec2 iam cloudtrail \
  --output-formats json-ocsf \
  --output-filename "$OUT_NAME" \
  --output-directory "$OUT_DIR" \
  --severity high critical \
  --no-banner >/dev/null 2>&1 || true

if [ ! -f "$OCSF" ]; then
  echo "ERROR: prowler produced no OCSF output at $OCSF" >&2
  exit 1
fi

echo ""
echo "== Findings (FAIL, HIGH+CRITICAL) =="
printf '%-10s %-55s %s\n' "SEVERITY" "CHECK" "RESOURCE"
jq -r '
  .[]
  | select(.status_code == "FAIL")
  | [ .severity,
      .finding_info.uid,
      (.resources[0].uid // .resources[0].name // "n/a")
    ] | @tsv' "$OCSF" \
| while IFS=$'\t' read -r sev check resource; do
    printf '%-10s %-55s %s\n' "$sev" "$check" "$resource"
  done

echo ""
echo "== Summary =="
FAIL=$(jq '[.[] | select(.status_code == "FAIL")] | length' "$OCSF")
echo "Total HIGH/CRITICAL FAIL findings: ${FAIL}"
