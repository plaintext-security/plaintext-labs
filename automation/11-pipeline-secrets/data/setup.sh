#!/usr/bin/env bash
# Seed: register the AWS-side trust for OIDC federation.
#   1. Create an IAM OIDC identity provider for our local issuer (the CI platform's
#      equivalent: in real life this is token.actions.githubusercontent.com).
#   2. Create a deploy role whose TRUST POLICY is scoped to exactly the intended
#      pipeline's audience (aud) and subject (sub = repo + branch). This scope is the
#      whole security control — a loose sub would let any fork/branch mint the credential.
#   3. Attach a tiny permission policy (what the pipeline may do once it has assumed the
#      role). Kept minimal — the lab is about *how the credential is obtained*, not its blast radius.
#
# Nothing here stores a long-lived AWS key for the pipeline. The runner gets its
# credential at job time via AssumeRoleWithWebIdentity. That is the point.
set -euo pipefail

ISSUER_HOST="oidc-provider:8080"               # our local OIDC issuer (host:port, no scheme for IAM)
ISSUER_URL="http://${ISSUER_HOST}"
ROLE_NAME="MeridianDeployRole"
LAB=/lab

echo "==> Registering IAM OIDC identity provider for ${ISSUER_URL}"
# Thumbprint is required by the API; LocalStack does not verify it against a real TLS
# cert (our issuer is plain HTTP in-lab), so a placeholder is accepted. In real AWS this
# is the SHA-1 of the issuer's TLS root CA cert.
awslocal iam create-open-id-connect-provider \
  --url "${ISSUER_URL}" \
  --client-id-list "sts.amazonaws.com" \
  --thumbprint-list "0000000000000000000000000000000000000000" \
  >/dev/null 2>&1 || echo "    (provider may already exist — continuing)"

PROVIDER_ARN="arn:aws:iam::000000000000:oidc-provider/${ISSUER_HOST}"
echo "    provider: ${PROVIDER_ARN}"

echo "==> Creating deploy role ${ROLE_NAME} with a SCOPED trust policy"
echo "    (aud = sts.amazonaws.com, sub = repo:meridian/api:ref:refs/heads/main only)"
awslocal iam create-role \
  --role-name "${ROLE_NAME}" \
  --assume-role-policy-document "file://${LAB}/data/trust-policy.json" \
  >/dev/null 2>&1 || \
awslocal iam update-assume-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-document "file://${LAB}/data/trust-policy.json" >/dev/null

echo "==> Attaching a minimal inline permission policy (what the pipeline may do)"
awslocal iam put-role-policy \
  --role-name "${ROLE_NAME}" \
  --policy-name "deploy-perms" \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:ListAllMyBuckets","s3:GetBucketLocation"],"Resource":"*"}]}' \
  >/dev/null

ROLE_ARN=$(awslocal iam get-role --role-name "${ROLE_NAME}" --query Role.Arn --output text)
echo "${ROLE_ARN}" > "${LAB}/data/role-arn.txt"
echo "==> Deploy role ready: ${ROLE_ARN}"
echo "==> Seed complete. The pipeline holds NO long-lived AWS key — it federates at runtime."
