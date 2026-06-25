FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# plaso (log2timeline/psort) pulls ~40 libyal C-extension dependencies that do
# not build cleanly from a pip sdist on a slim image. The maintainers' GIFT
# "stable" PPA ships plaso-tools and every libyal dep prebuilt for jammy on both
# amd64 and arm64 — the canonical, reproducible install path. Keep the PPA setup
# and the plaso-tools install in separate apt transactions so the PPA index is
# fully refreshed before resolving plaso's dependency graph.
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    ca-certificates \
    gnupg \
    python3 \
    && rm -rf /var/lib/apt/lists/*

RUN add-apt-repository -y ppa:gift/stable \
    && apt-get update \
    && apt-get install -y --no-install-recommends plaso-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /lab
COPY . /lab/
