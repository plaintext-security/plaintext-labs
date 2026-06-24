FROM debian:bookworm-slim

ARG DEBIAN_FRONTEND=noninteractive

# Toolchain: Python + ldap3 (the deterministic wave gate over the seed JSON AND the LIVE
# corroboration `make corroborate` that reads real rosters/SPNs off the bundled Samba DC) plus
# ldap-utils for ad-hoc ldapsearch. The GPO-logon ENFORCEMENT remains modelled — see VALIDATION.md.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    ldap-utils \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir ldap3

WORKDIR /lab
COPY . /lab
