# Reference lab image: Sigma tooling + PyYAML for the ZT monitoring/detection lab.
# Identical toolchain to defensive/08-detection-as-code — sigma-cli for conversion,
# PyYAML for the offline teaching matcher (detect.py).
FROM python:3.12-slim

RUN pip install --no-cache-dir \
      sigma-cli==1.0.4 \
      pysigma-backend-splunk==1.1.0 \
      pysigma-pipeline-sysmon==1.0.4 \
      pyyaml==6.0.2

WORKDIR /lab
COPY . /lab

CMD ["bash"]
