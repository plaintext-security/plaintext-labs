# Module 17 — Data Protection & KMS
# awscli + openssl (local envelope encryption) + Python 3.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl unzip jq openssl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# awscli (v1, via pip). v1 is pure Python, so it works on both amd64 and arm64
# (the v2 binary is x86_64-only and fails under emulation on Apple Silicon). v1 honors
# AWS_ENDPOINT_URL, so plain `aws` targets floci or real AWS with no LocalStack-branded wrapper.
RUN pip install --no-cache-dir awscli==1.33.44

ENV AWS_ACCESS_KEY_ID=test \
    AWS_SECRET_ACCESS_KEY=test \
    AWS_DEFAULT_REGION=us-east-1

WORKDIR /lab
COPY . /lab

CMD ["bash"]
