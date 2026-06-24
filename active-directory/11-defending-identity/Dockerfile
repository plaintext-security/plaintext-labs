FROM debian:bookworm-slim

ARG DEBIAN_FRONTEND=noninteractive

# Toolchain for the tiered-admin compliance check: Python + ldap3 (tier-compliance-check.py reads
# the live group rosters off the DC) plus samba-tool/ldap-utils for ad-hoc remediation and queries.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    ldap-utils \
    samba \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir ldap3

WORKDIR /lab
COPY . /lab
