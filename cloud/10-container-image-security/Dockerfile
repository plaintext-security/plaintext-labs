# Lab container: trivy + grype so `make shell` gives you both tools.
# We copy the binaries straight from the official tool images (multi-arch, pinned) —
# the vendor install.sh scripts and loose release-asset names break across versions/arches.
FROM aquasec/trivy:0.51.2 AS trivybin
FROM anchore/grype:v0.76.0 AS grypebin

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    jq \
    && rm -rf /var/lib/apt/lists/*

COPY --from=trivybin /usr/local/bin/trivy /usr/local/bin/trivy
COPY --from=grypebin /grype /usr/local/bin/grype

WORKDIR /lab
