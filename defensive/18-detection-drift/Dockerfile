# Reference lab image: detection / telemetry drift harness.
# - PyYAML → parse the baseline manifest and the Sigma rule
# (No SIEM needed: the drift loop runs offline against bundled JSONL.)
FROM python:3.12-slim

RUN pip install --no-cache-dir pyyaml==6.0.2

WORKDIR /lab
COPY . /lab

CMD ["bash"]
