# Module 13 — Fleet Migration
# Reuses Module 06's Ansible-controller shape. To keep the lab deterministic,
# zero-cost, and CI-runnable end-to-end without fragile inter-container SSH, the
# "fleet" is modelled as N per-host state directories under /fleet, each running
# a tiny HTTP health endpoint (an in-service app), all inside this one controller
# container. The rollout script applies the Module-06 baseline ring by ring with
# serial / max_fail_percentage and a pre/post service-health gate.
FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 \
      python3-pip \
      openssh-client \
      sudo \
      less \
      jq \
      curl \
      procps \
      iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Ansible via pip (pinned to match Module 06) — used for the rolling playbook.
RUN pip3 install --no-cache-dir ansible==9.4.0

RUN mkdir -p /lab
COPY . /lab
RUN chmod +x /lab/*.sh /lab/data/*.sh 2>/dev/null || true

WORKDIR /lab
CMD ["bash"]
