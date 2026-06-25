# Velociraptor on a clean Debian base, built for the host's architecture.
#
# The community wlambert/velociraptor image is amd64-only and does not place a
# `velociraptor` binary on PATH (the entry binary lives under /opt), so the
# compose commands here (`velociraptor ...`) failed with exit 127 on arm64.
# We instead download the official, signed release binary for the build arch
# (amd64 or arm64) and install it as /usr/local/bin/velociraptor so the lab
# runs natively on both Intel and Apple-silicon hosts.
FROM debian:12-slim

ARG TARGETARCH
ARG VELO_VERSION=v0.77.1

RUN apt-get update -qq \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && rm -rf /var/lib/apt/lists/* \
 && case "${TARGETARCH}" in \
      amd64) VELO_ARCH=amd64 ;; \
      arm64) VELO_ARCH=arm64 ;; \
      *)     echo "unsupported arch: ${TARGETARCH}" >&2; exit 1 ;; \
    esac \
 && curl -fsSL -o /usr/local/bin/velociraptor \
      "https://github.com/Velocidex/velociraptor/releases/download/${VELO_VERSION}/velociraptor-${VELO_VERSION}-linux-${VELO_ARCH}" \
 && chmod +x /usr/local/bin/velociraptor \
 && velociraptor version

WORKDIR /velociraptor
