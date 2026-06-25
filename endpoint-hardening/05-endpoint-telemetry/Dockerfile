# Module 05 — Endpoint Telemetry & EDR
# Ubuntu 22.04 with osquery daemon
FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG OSQUERY_VERSION=5.12.1
ARG TARGETARCH

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      wget \
      gnupg \
      apt-transport-https \
      python3 \
      python3-pip \
      jq \
      less \
      procps \
      net-tools \
      cron \
    && rm -rf /var/lib/apt/lists/*

# Install osquery from the pinned GitHub release (cross-arch; TARGETARCH injected by BuildKit: amd64|arm64)
RUN curl -fsSL \
      "https://github.com/osquery/osquery/releases/download/${OSQUERY_VERSION}/osquery_${OSQUERY_VERSION}-1.linux_${TARGETARCH}.deb" \
      -o /tmp/osquery.deb && \
    dpkg -i /tmp/osquery.deb && rm /tmp/osquery.deb

WORKDIR /lab
COPY . /lab

CMD ["bash"]
