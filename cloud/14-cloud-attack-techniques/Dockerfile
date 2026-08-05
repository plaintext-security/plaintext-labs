# Lab 14 — Cloud Attack Techniques
# Provides: awscli (honors AWS_ENDPOINT_URL), jq, python3, and a pinned Stratus Red Team binary.
FROM python:3.12-slim

ARG STRATUS_VERSION=2.16.0

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      jq \
      unzip \
      uuid-runtime \
    && rm -rf /var/lib/apt/lists/*

# awscli v2 (static binary) — arch-aware so the image works on amd64 and arm64.
RUN case "$(uname -m)" in \
      x86_64)  AWSCLI_ARCH=x86_64 ;; \
      aarch64|arm64) AWSCLI_ARCH=aarch64 ;; \
      *) echo "Unsupported architecture: $(uname -m)" >&2; exit 1 ;; \
    esac \
    && curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-${AWSCLI_ARCH}.zip" -o /tmp/awscliv2.zip \
    && unzip -q /tmp/awscliv2.zip -d /tmp \
    && /tmp/aws/install \
    && rm -rf /tmp/aws /tmp/awscliv2.zip

# Stratus Red Team — prebuilt binary for linux/amd64
RUN curl -fsSL \
    "https://github.com/DataDog/stratus-red-team/releases/download/v${STRATUS_VERSION}/stratus-red-team_Linux_x86_64.tar.gz" \
    -o /tmp/stratus.tar.gz \
    && tar -xzf /tmp/stratus.tar.gz -C /usr/local/bin stratus \
    && chmod +x /usr/local/bin/stratus \
    && rm /tmp/stratus.tar.gz

WORKDIR /lab
COPY . /lab

# Default AWS env vars pointing at floci (overridable)
ENV AWS_DEFAULT_REGION=us-east-1 \
    AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE \
    AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
    AWS_ENDPOINT_URL=http://floci:4566

RUN chmod +x /lab/simulate.sh

CMD ["bash"]
