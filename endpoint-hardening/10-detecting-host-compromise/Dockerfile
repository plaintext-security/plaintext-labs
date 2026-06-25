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

# sigma-cli (modern pysigma -> pyparsing>=3.1) and python-evtx (pins pyparsing==2.4.7)
# have mutually exclusive pyparsing requirements, so they cannot share one
# environment. They are never used in the same process — sigma-cli converts/matches
# rules, evtx_dump.py only renders EVTX to XML in the `convert` step — so install
# python-evtx into its own isolated venv and expose evtx_dump.py on PATH.
RUN pip install --no-cache-dir \
      sigma-cli==1.0.1 \
      pysigma-backend-splunk==1.1.0 \
      pysigma-backend-elasticsearch==1.1.4 \
      pyyaml==6.0.1

RUN python3 -m venv /opt/evtx-venv && \
    /opt/evtx-venv/bin/pip install --no-cache-dir python-evtx==0.7.4 && \
    ln -s /opt/evtx-venv/bin/evtx_dump.py /usr/local/bin/evtx_dump.py

# Create rules directory
RUN mkdir -p /lab/rules

WORKDIR /lab
COPY . /lab

CMD ["bash"]
