# Lab 15 — Cloud Logging & Detection
# Provides: Python 3.12, PyYAML (for Sigma rule parsing), pysigma tooling.
FROM python:3.12-slim

RUN pip install --no-cache-dir \
      pyyaml==6.0.2 \
      sigma-cli==1.0.4 \
      pysigma-backend-splunk==1.1.0 \
      pysigma-pipeline-sysmon==1.0.4

WORKDIR /lab
COPY . /lab

CMD ["bash"]
