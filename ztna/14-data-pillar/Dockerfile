# Reference lab image: Sigma tooling + PyYAML for the Data pillar lab.
# Identical toolchain to ztna/09-monitoring-detection — sigma-cli for conversion,
# PyYAML for the offline teaching matcher (detect.py, extended here with a count
# aggregation for bulk-restricted-read detection).
FROM python:3.12-slim

RUN pip install --no-cache-dir \
      sigma-cli==1.0.4 \
      pysigma-backend-splunk==1.1.0 \
      pysigma-pipeline-sysmon==1.0.4 \
      pyyaml==6.0.2

WORKDIR /lab
COPY . /lab

CMD ["bash"]
