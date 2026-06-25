# Module 08 — Patch & Vulnerability Management
# Ubuntu 22.04 with osquery + grype; intentionally pinned older packages for CVE demo
FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG OSQUERY_VERSION=5.12.1
ARG GRYPE_VERSION=0.74.7
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
    && rm -rf /var/lib/apt/lists/*

# Install osquery from the pinned GitHub release (cross-arch; TARGETARCH injected by BuildKit: amd64|arm64)
RUN curl -fsSL \
      "https://github.com/osquery/osquery/releases/download/${OSQUERY_VERSION}/osquery_${OSQUERY_VERSION}-1.linux_${TARGETARCH}.deb" \
      -o /tmp/osquery.deb && \
    dpkg -i /tmp/osquery.deb && rm /tmp/osquery.deb

# Install grype
RUN curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh \
      | sh -s -- -b /usr/local/bin v${GRYPE_VERSION}

WORKDIR /lab
COPY . /lab

CMD ["bash"]
