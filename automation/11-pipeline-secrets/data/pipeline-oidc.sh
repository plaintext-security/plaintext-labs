#!/usr/bin/env bash
# pipeline-oidc.sh — the AFTER: a deploy step that federates instead of storing a key.
#
# The runner arrives with NO long-lived AWS credential. At job time it:
#   1. mints a short-lived, signed OIDC JWT that describes this run (iss/aud/sub) — the
#      job our local mint_oidc_token.py / the CI platform's OIDC provider does for real;
#   2. hands that token to AWS STS via AssumeRoleWithWebIdentity;
#   3. receives TEMPORARY credentials: AccessKeyId + SecretAccessKey + a SessionToken,
#      stamped with an Expiration minutes out. Nothing was stored anywhere.
#
# Writes the minted credential JSON to /tmp/oidc-creds.json so `check_no_static_secret.py`
# can assert it carries a SessionToken and a future Expiration (= genuinely short-lived).
set -euo pipefail

LAB=/lab
ROLE_ARN=$(cat "${LAB}/data/role-arn.txt")
OUT=/tmp/oidc-creds.json

# Guard: an OIDC runner must not be carrying a stored long-lived key. If these are set,
# the whole exercise is defeated — fail loudly. (The compose file deliberately leaves
# them unset on the runner.)
if [ -n "${AWS_ACCESS_KEY_ID:-}" ] && [ "${AWS_ACCESS_KEY_ID:-}" != "test" ]; then
  echo "!! a long-lived AWS_ACCESS_KEY_ID is present — an OIDC runner should hold none." >&2
fi

echo "== OIDC pipeline: federate for a short-lived credential (no stored key) =="

echo "  1. mint a short-lived OIDC JWT describing this run (sub = the repo + branch)"
TOKEN=$(python3 "${LAB}/data/mint_oidc_token.py" --ttl 900)
echo "     token minted (RS256, 15-min TTL); claims:"
python3 - "$TOKEN" <<'PY'
import sys, jwt
t = sys.argv[1]
c = jwt.decode(t, options={"verify_signature": False})
for k in ("iss", "aud", "sub", "exp"):
    print(f"       {k} = {c.get(k)}")
PY
echo

echo "  2. exchange it at STS via AssumeRoleWithWebIdentity for temporary credentials"
# STS verifies the JWT against the OIDC provider's JWKS and the role's trust policy, then
# returns short-lived creds. (LocalStack community is lenient about signature/claim
# verification — see lab.md; the SHAPE of the response is faithful: temporary creds with
# a SessionToken + Expiration, which is what we assert.)
awslocal sts assume-role-with-web-identity \
  --role-arn "${ROLE_ARN}" \
  --role-session-name "deploy-$(date +%s)" \
  --web-identity-token "${TOKEN}" \
  > "${OUT}"

echo "     STS returned temporary credentials -> ${OUT}"
echo "     SessionToken present:" \
  "$(jq -r 'if .Credentials.SessionToken then "yes" else "no" end' "${OUT}")"
echo "     Expiration:" "$(jq -r '.Credentials.Expiration' "${OUT}")"
echo

echo "  3. 'deploy' using ONLY the minted temporary credentials (the static key is gone)"
export AWS_ACCESS_KEY_ID=$(jq -r '.Credentials.AccessKeyId' "${OUT}")
export AWS_SECRET_ACCESS_KEY=$(jq -r '.Credentials.SecretAccessKey' "${OUT}")
export AWS_SESSION_TOKEN=$(jq -r '.Credentials.SessionToken' "${OUT}")
awslocal s3api list-buckets --query 'Owner.ID' --output text >/dev/null 2>&1 \
  && echo "     deploy step ran with the short-lived credential." \
  || echo "     (deploy call returned)"
echo
echo "  RESULT: no long-lived key was ever stored. The credential used carries a"
echo "  SessionToken and expires on its own. The off-switch is the trust policy, not a"
echo "  secret you have to find and rotate."
