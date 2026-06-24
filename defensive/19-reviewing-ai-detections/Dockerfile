# Reference lab image: review AI-drafted Sigma detections.
# - sigma-cli + Splunk backend → prove each rule still *converts* cleanly (the
#   point being that conversion passing is NOT the same as the rule being correct)
# - PyYAML → used by the bundled review harness (review.py)
FROM python:3.12-slim

RUN pip install --no-cache-dir \
      sigma-cli==1.0.4 \
      pysigma-backend-splunk==1.1.0 \
      pysigma-pipeline-sysmon==1.0.4 \
      pyyaml==6.0.2

WORKDIR /lab
COPY . /lab

CMD ["bash"]
