# Module 10 — Workload Identity & mTLS (SPIFFE/SPIRE)
# One image used for every service in the lab: it carries both SPIRE binaries
# (server + agent) plus a shell, openssl, and jq — so the daemons, the bootstrap
# step, and the workloads all run from the same place and stay legible.
#
# The SPIRE binaries are copied out of the official upstream images; the runtime
# is plain debian-slim so we have bash/openssl for the workload mTLS steps.
FROM ghcr.io/spiffe/spire-server:1.9.6 AS server
FROM ghcr.io/spiffe/spire-agent:1.9.6 AS agent

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
      bash openssl curl jq ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=server /opt/spire/bin/spire-server /usr/local/bin/spire-server
COPY --from=agent  /opt/spire/bin/spire-agent  /usr/local/bin/spire-agent

WORKDIR /opt/spire
CMD ["bash"]
