# Lab 02 — Cloud Identity & IAM
# Provides: cloudfox (pre-built binary) + awscli v2 (honors AWS_ENDPOINT_URL) + boto3
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      unzip \
      jq \
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

# boto3 (used by cloudfox-style enumeration and helper scripts)
RUN pip install --no-cache-dir boto3==1.34.144

# cloudfox — BishopFox's cloud enumeration tool (pre-built Linux binary)
ARG CLOUDFOX_VERSION=1.14.0
RUN curl -fsSL \
      "https://github.com/BishopFox/cloudfox/releases/download/v${CLOUDFOX_VERSION}/cloudfox-linux-amd64.zip" \
      -o /tmp/cloudfox.zip \
    && unzip /tmp/cloudfox.zip -d /usr/local/bin \
    && chmod +x /usr/local/bin/cloudfox \
    && rm /tmp/cloudfox.zip

# Dummy credentials for the emulator (ignored by floci, but required by the CLI)
ENV AWS_ACCESS_KEY_ID=test \
    AWS_SECRET_ACCESS_KEY=test \
    AWS_DEFAULT_REGION=us-east-1

# Configure a named profile so cloudfox --profile local works
RUN mkdir -p /root/.aws && printf \
      "[profile local]\nregion = us-east-1\noutput = json\n" \
      >> /root/.aws/config \
    && printf \
      "[local]\naws_access_key_id = test\naws_secret_access_key = test\n" \
      >> /root/.aws/credentials

WORKDIR /lab
COPY . /lab

CMD ["bash"]
