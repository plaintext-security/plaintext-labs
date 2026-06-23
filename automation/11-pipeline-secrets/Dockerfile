# Module 11 — Secrets Handling in Pipelines (OIDC)
# A runner-like image: awslocal (LocalStack wrapper for the AWS CLI), openssl + python
# (to mint and sign an OIDC-style JWT and serve a tiny JWKS), and jq.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl unzip jq openssl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# awscli (v1, via pip) + awslocal. v1 is pure Python, so it works on both amd64 and
# arm64 (the v2 binary is x86_64-only and fails under emulation on Apple Silicon).
# PyJWT + cryptography let us mint a real RS256-signed token and publish its JWKS,
# so the OIDC flow is legible end-to-end rather than a black box.
RUN pip install --no-cache-dir \
      awscli==1.33.44 awscli-local==0.22.0 \
      "PyJWT[crypto]==2.9.0" cryptography==43.0.1

ENV AWS_ACCESS_KEY_ID=test \
    AWS_SECRET_ACCESS_KEY=test \
    AWS_DEFAULT_REGION=us-east-1

WORKDIR /lab
COPY . /lab

CMD ["bash"]
