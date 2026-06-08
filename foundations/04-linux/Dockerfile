FROM ubuntu:22.04
RUN apt-get update -qq && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        procps sudo python3 findutils grep gawk coreutils \
    && rm -rf /var/lib/apt/lists/*

# Plant some users for the triage exercise
RUN useradd -m -s /bin/bash jsmith && \
    useradd -m -s /bin/bash mchen && \
    useradd -m -s /bin/bash deploy && \
    useradd -m -s /bin/false svc-backup && \
    echo "jsmith ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

WORKDIR /lab
COPY data/ data/
COPY demo.py .
