# zeek/zeek dropped the "-ubuntu" tag suffix; current tags are multi-arch
# (amd64 + arm64) and Debian-based. Pin a recent stable release.
FROM zeek/zeek:7.2.2

# On the Debian base, scapy is packaged as python3-scapy (the bare "scapy"
# apt name only existed on the old Ubuntu image).
RUN apt-get update && apt-get install -y \
    tshark \
    python3 \
    python3-pip \
    python3-scapy \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /lab
COPY scripts/ /scripts/

# Note: /data is provided at runtime by the compose bind-mount (./data:/data);
# the captures live there and are generated/fetched, not baked into the image
# (and data/ is gitignored, so it does not exist on a clean clone at build time).
RUN mkdir -p /data && chmod +x /scripts/*.sh
