FROM debian:bookworm-slim

ARG DEBIAN_FRONTEND=noninteractive

# Minimal toolchain for the deterministic tiering SIMULATION: Python (graph/attack-path
# checks over the seed JSON) plus ldap-utils so a learner extending toward a real Samba DC
# has ldapsearch on hand. No live DC is provisioned here — see VALIDATION.md for the gap.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    ldap-utils \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /lab
COPY . /lab
