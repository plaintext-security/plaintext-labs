# Reference lab image: Sigma tooling for detection-as-code.
# - sigma-cli + the Splunk backend → convert a rule to a real SIEM query
# - PyYAML → used by the bundled teaching matcher (detect.py)
FROM python:3.12-slim

RUN pip install --no-cache-dir \
      sigma-cli==1.0.4 \
      pysigma-backend-splunk==1.1.0 \
      pysigma-pipeline-sysmon==1.0.4 \
      pyyaml==6.0.2

WORKDIR /lab
COPY . /lab

CMD ["bash"]
