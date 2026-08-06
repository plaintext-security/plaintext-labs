# Lab 01 — Cloud Fundamentals & Shared Responsibility
# Provides: awscli v2 (honors AWS_ENDPOINT_URL -> floci or real AWS) + Python 3
FROM python:3.12-slim

# aws-cli v2 is not on PyPI; install the official binary bundle.
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      unzip \
      groff \
      less \
      jq \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI v2 (official binary, pinned version).
# Pick the bundle that matches the build architecture so the image works on
# both amd64 hosts and arm64 (Apple Silicon) without emulation crashes.
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

# Fake default credentials for the floci route (the emulator ignores them; the
# real-AWS route overrides these with your own credentials from the environment).
ENV AWS_ACCESS_KEY_ID=test \
    AWS_SECRET_ACCESS_KEY=test \
    AWS_DEFAULT_REGION=us-east-1

WORKDIR /lab
COPY . /lab

CMD ["bash"]
