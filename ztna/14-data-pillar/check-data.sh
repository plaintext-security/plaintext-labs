#!/usr/bin/env bash
# check-data.sh — regression test for Lab 14 (Data, the Last Pillar).
#
# Asserts:
#   1. A merely-authenticated, non-privileged role (analyst) reading a RESTRICTED
#      record is DENIED — the label-based deny fires.
#   2. FAIL-CLOSED: a record with a missing/unknown classification label resolves to
#      "restricted", not "public" — and a non-privileged role is denied reading it.
#   3. A privileged role (data-officer) reading restricted data is ALLOWED — the
#      policy isn't just deny-everything.
#   4. The bulk-restricted-read Sigma rule FIRES on the anomalous overnight session
#      (sess_D2, 8 reads) and stays SILENT on the same user's normal daytime session
#      (sess_D1, 3 reads) — exfil-shaped access is a volume signal, not an identity one.
#
# Run from the lab dir after `make up`:  bash check-data.sh   (or: make check)
set -uo pipefail

pass=0; fail=0
ok()  { echo "  PASS  $1"; pass=$((pass+1)); }
bad() { echo "  FAIL  $1"; fail=$((fail+1)); }

opa_eval() { # $1 = input path, $2 = query suffix (allow / deny / effective_classification)
  docker compose run --rm opa-lab eval \
    --input "/lab/$1" \
    --data /lab/data/policies/data-classification.rego \
    "data.corp.data.$2" 2>/dev/null
}

echo "== 1. Label-based deny: analyst reading RESTRICTED must be denied =="
out="$(opa_eval data/inputs/analyst-read-restricted.json deny)"
if echo "$out" | grep -q '"value": true'; then
  ok "analyst -> restricted: deny fired"
else
  bad "analyst -> restricted: deny did NOT fire"
fi

echo "== 2. Fail-closed: unlabeled record resolves to restricted, not public =="
out="$(opa_eval data/inputs/analyst-read-unlabeled.json effective_classification)"
if echo "$out" | grep -q '"value": "restricted"'; then
  ok "unlabeled record -> effective_classification = restricted"
else
  bad "unlabeled record did NOT resolve to restricted"
fi

out="$(opa_eval data/inputs/analyst-read-unlabeled.json deny)"
if echo "$out" | grep -q '"value": true'; then
  ok "analyst -> unlabeled record: deny fired (fail-closed, not fail-open)"
else
  bad "analyst -> unlabeled record: deny did NOT fire"
fi

echo "== 3. Sanity: a privileged role is still allowed (this isn't deny-everything) =="
out="$(opa_eval data/inputs/data-officer-read-restricted.json allow)"
if echo "$out" | grep -q '"value": true'; then
  ok "data-officer -> restricted: allowed"
else
  bad "data-officer -> restricted: should be allowed, was not"
fi

echo "== 4. Exfil detection: bulk restricted reads fire, normal reads stay silent =="
det_out="$(docker compose run --rm sigma python detect.py \
  examples/zt-bulk-restricted-read.yml data/access-logs.jsonl 2>/dev/null)"
hit_count="$(echo "$det_out" | grep -c '\[HIT\]')"
if [ "$hit_count" -eq 8 ] && echo "$det_out" | grep -q 'session_id=sess_D2'; then
  ok "bulk session sess_D2 (8 restricted reads) fired, exactly 8 hits"
else
  bad "expected exactly 8 hits on sess_D2, got $hit_count -- $(echo "$det_out" | tail -3)"
fi
if echo "$det_out" | grep -q 'sess_D1'; then
  bad "normal session sess_D1 (3 restricted reads) fired -- should be silent"
else
  ok "normal session sess_D1 (3 restricted reads) stayed silent"
fi

echo ""
echo "== ${pass} passed, ${fail} failed =="
[ "$fail" -eq 0 ]
