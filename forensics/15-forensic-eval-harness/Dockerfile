# Reference lab image: a forensic detection-rule eval harness.
# - python3 + PyYAML → run eval.py and load the timestomp/YARA detector configs
# - yara            → score the real Module-12 YARA rule over the bundled PE fixtures,
#                     so the "loosen a string and watch precision collapse" demo uses a
#                     genuine yara binary, not a simulation.
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-yaml \
    yara \
    && rm -rf /var/lib/apt/lists/*

COPY scripts/ /scripts/
COPY data/ /data/
COPY regressed/ /regressed/

RUN chmod +x /scripts/*.py /scripts/*.sh 2>/dev/null || true

WORKDIR /lab
