# Module 12 — Configuration & Posture Drift
# Reuses Module 06's Ansible-controller + localhost-target shape: a single
# privileged container is BOTH the Ansible controller and the hardened target
# (ansible_connection=local), so the whole detect -> diff -> reconcile -> alert
# loop stands up in Docker with zero cloud cost and no inter-container SSH.
FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 \
      python3-pip \
      openssh-client \
      openssh-server \
      sudo \
      auditd \
      libpam-pwquality \
      libopenscap8 \
      less \
      jq \
      cron \
      curl \
    && rm -rf /var/lib/apt/lists/*

# Ansible via pip (pinned to match Module 06)
RUN pip3 install --no-cache-dir ansible==9.4.0

# SSH bits so sshd_config exists for the PermitRootLogin control/drift
RUN mkdir -p /run/sshd && \
    ssh-keygen -A && \
    grep -q '^PermitRootLogin' /etc/ssh/sshd_config || echo "PermitRootLogin no" >> /etc/ssh/sshd_config

# Inventory: localhost is both controller and target (Module 06 pattern)
RUN mkdir -p /lab
COPY . /lab
RUN printf '[target]\nlocalhost ansible_connection=local\n' > /lab/inventory && \
    chmod +x /lab/data/*.sh 2>/dev/null || true

WORKDIR /lab
CMD ["bash"]
