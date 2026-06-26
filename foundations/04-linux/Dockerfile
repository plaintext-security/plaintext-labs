FROM ubuntu:22.04
RUN apt-get update -qq && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        procps sudo python3 findutils grep gawk coreutils \
    && rm -rf /var/lib/apt/lists/*

# Plant some users for the triage exercise. jsmith holds a NOPASSWD:ALL sudo
# entry — the "surprisingly broad" privilege the log will tie a compromise to.
RUN useradd -m -s /bin/bash jsmith && \
    useradd -m -s /bin/bash mchen && \
    useradd -m -s /bin/bash deploy && \
    useradd -m -s /bin/false svc-backup && \
    echo "jsmith ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Post-compromise persistence: a SUID-root shell the attacker dropped after
# brute-forcing jsmith and using its NOPASSWD root to plant it. THIS is the SUID
# sweep's payoff — a root-owned SUID binary outside the distro's set, in an
# unusual location with a hidden-ish name, and it's bash (GTFOBins: `bash -p`
# returns an instant root shell). It ties pass 2 to the rest of the investigation.
RUN cp /bin/bash /usr/local/bin/.cache-helper && \
    chown root:root /usr/local/bin/.cache-helper && \
    chmod 4755 /usr/local/bin/.cache-helper

WORKDIR /lab
COPY data/ data/
COPY demo.py .
