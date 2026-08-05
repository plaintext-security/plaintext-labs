# Lab 03 — IAM Attack Paths
# Provides: Python 3 (analyze.py) + awscli v2 (honors AWS_ENDPOINT_URL) + pmapper
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      unzip \
      jq \
      git \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# AWS CLI v2 — pick the bundle matching the build arch so the image works on both
# amd64 and arm64 (Apple Silicon) without x86_64-under-emulation crashes.
ARG AWSCLI_VERSION=2.17.20
RUN case "$(uname -m)" in \
      x86_64)  AWSCLI_ARCH=x86_64 ;; \
      aarch64|arm64) AWSCLI_ARCH=aarch64 ;; \
      *) echo "Unsupported architecture: $(uname -m)" >&2; exit 1 ;; \
    esac \
    && curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-${AWSCLI_ARCH}-${AWSCLI_VERSION}.zip" \
      -o /tmp/awscliv2.zip \
    && unzip /tmp/awscliv2.zip -d /tmp \
    && /tmp/aws/install \
    && rm -rf /tmp/awscliv2.zip /tmp/aws

# boto3 + principal-mapper (pmapper)
RUN pip install --no-cache-dir \
      boto3==1.34.144 \
      principalmapper==1.1.5

# Dummy credentials for the emulator (ignored by floci, but required by the CLI)
ENV AWS_ACCESS_KEY_ID=test \
    AWS_SECRET_ACCESS_KEY=test \
    AWS_DEFAULT_REGION=us-east-1

RUN mkdir -p /root/.aws && printf \
      "[profile local]\nregion = us-east-1\noutput = json\n" \
      >> /root/.aws/config \
    && printf \
      "[local]\naws_access_key_id = test\naws_secret_access_key = test\n" \
      >> /root/.aws/credentials

WORKDIR /lab
COPY . /lab

CMD ["bash"]
