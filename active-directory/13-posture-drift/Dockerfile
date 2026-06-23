FROM debian:bookworm-slim

ARG DEBIAN_FRONTEND=noninteractive

# Toolchain for the deterministic drift SIMULATION: Python3 (the detect->diff loop over the
# seed posture), cron (to schedule the detector — the "is it STILL hardened?" question), bash
# (the drift-introduce mutator), and ldap-utils for a learner extending toward a live Samba DC.
# Adalanche (the attack-graph corroboration step in lab.md) is NOT bundled — it needs a live
# DC to ingest; see VALIDATION.md for how the graph view fits the real-DC variant.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    cron \
    bash \
    ldap-utils \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /lab
COPY . /lab
RUN chmod +x bin/drift-introduce.sh
