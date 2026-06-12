#!/usr/bin/env bash
# pipeline-bad.sh — the BEFORE: a deploy step that authenticates with a STORED long-lived key.
#
# This is the pattern the whole track keeps hunting with gitleaks/trufflehog. The runner
# is handed two long strings (an AWS access key id + secret) that ARE a standing IAM
# principal: no expiry, copied wherever this job runs, surviving every incident until a
# human rotates them. They have to live *somewhere* a CI job can read — a CI secret, an
# env var, a .env file — and that "somewhere" is the leak surface.
#
# Here we simulate the stored credential as env vars set right before the deploy. Note
# what you can prove about this pipeline: there IS a long-lived key present, and the
# identity it uses NEVER expires.
set -euo pipefail

echo "== BAD pipeline: deploy using a STORED long-lived access key =="

# The stored credential. In a real repo this is a CI secret / .env / tfvars — exactly
# what gitleaks flags. (These are LocalStack's dummy creds; the point is the *pattern*.)
export AWS_ACCESS_KEY_ID="AKIAEXAMPLE1234ABCD5"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMIexampleStaticSecretKeyDoNotUse"

echo "  the runner now holds a long-lived key:"
echo "    AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}"
echo "    AWS_SECRET_ACCESS_KEY=<stored secret, no expiry>"
echo

echo "  'deploying' (listing buckets) with the static key..."
awslocal s3api list-buckets --query 'Owner.ID' --output text >/dev/null 2>&1 \
  && echo "    deploy step ran." || echo "    (deploy call returned; LocalStack creds are permissive)"
echo

echo "  PROBLEM: this credential has no SessionToken and no Expiration — it is standing,"
echo "  ambient authority that lives until rotated. If it leaks, it is valid until someone"
echo "  notices and rotates it everywhere. The fix is to STOP STORING IT (see pipeline-oidc.sh)."
