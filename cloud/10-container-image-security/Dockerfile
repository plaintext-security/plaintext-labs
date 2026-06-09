# Lab container: trivy + grype installed so `make shell` gives you both tools.
# Pinned to a small base; both tools are pulled as static binaries.
FROM debian:bookworm-slim

ARG TRIVY_VERSION=0.51.2
ARG GRYPE_VERSION=0.76.0

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install trivy
RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
    | sh -s -- -b /usr/local/bin v${TRIVY_VERSION}

# Install grype
RUN curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh \
    | sh -s -- -b /usr/local/bin v${GRYPE_VERSION}

WORKDIR /lab
