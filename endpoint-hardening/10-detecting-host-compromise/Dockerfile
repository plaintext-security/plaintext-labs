# Module 10 — Detecting Host Compromise
# Python container with sigma-cli, python-evtx (evtx_dump.py), PyYAML.
# Telemetry is REAL Windows EVTX from sbousseaden/EVTX-ATTACK-SAMPLES,
# staged from the shared cache by fetch-data.sh and converted to JSON in-container.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      jq \
      less \
    && rm -rf /var/lib/apt/lists/*

# Install sigma-cli, python-evtx (provides evtx_dump.py), and dependencies
RUN pip install --no-cache-dir \
      sigma-cli==1.0.1 \
      pysigma-backend-splunk==1.0.3 \
      pysigma-backend-elasticsearch==1.1.2 \
      python-evtx==0.7.4 \
      pyyaml==6.0.1

# Create rules directory
RUN mkdir -p /lab/rules

WORKDIR /lab
COPY . /lab

CMD ["bash"]
