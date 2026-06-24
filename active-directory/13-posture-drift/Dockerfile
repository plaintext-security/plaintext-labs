FROM debian:bookworm-slim

ARG DEBIAN_FRONTEND=noninteractive

# Toolchain for both drift modes: Python3 + ldap3 (the detect->diff loop, and the LIVE collector
# `--live`/`make detect-live` that reads posture straight off the Samba DC), cron (to schedule the
# detector — the "is it STILL hardened?" question), bash (the drift-introduce mutator), and
# ldap-utils for ad-hoc ldapsearch. Adalanche (the attack-graph corroboration step in lab.md) is
# NOT bundled — see VALIDATION.md for how the graph view fits the real-DC variant.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    cron \
    bash \
    ldap-utils \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir ldap3

WORKDIR /lab
COPY . /lab
RUN chmod +x bin/drift-introduce.sh
