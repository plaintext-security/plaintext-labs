# Module 06 — PKI & Certificate Management
# step-ca + step CLI
FROM debian:12-slim

ARG STEP_CA_VERSION=0.28.4
ARG STEP_CLI_VERSION=0.28.7
# TARGETARCH (amd64 / arm64) is provided automatically by buildkit for the build platform.
ARG TARGETARCH

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      wget \
      openssl \
      jq \
      less \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install step CLI
RUN wget -q "https://github.com/smallstep/cli/releases/download/v${STEP_CLI_VERSION}/step_linux_${STEP_CLI_VERSION}_${TARGETARCH}.tar.gz" \
      -O /tmp/step.tar.gz && \
    tar -xzf /tmp/step.tar.gz -C /tmp && \
    mv /tmp/step_${STEP_CLI_VERSION}/bin/step /usr/local/bin/step && \
    rm -rf /tmp/step.tar.gz /tmp/step_${STEP_CLI_VERSION}

# Install step-ca (recent release tarballs ship the binary at the archive root)
RUN wget -q "https://github.com/smallstep/certificates/releases/download/v${STEP_CA_VERSION}/step-ca_linux_${STEP_CA_VERSION}_${TARGETARCH}.tar.gz" \
      -O /tmp/step-ca.tar.gz && \
    tar -xzf /tmp/step-ca.tar.gz -C /tmp step-ca && \
    mv /tmp/step-ca /usr/local/bin/step-ca && \
    rm -f /tmp/step-ca.tar.gz

# Create step user
RUN useradd -m -s /bin/bash step

WORKDIR /lab
COPY . /lab

CMD ["bash"]
