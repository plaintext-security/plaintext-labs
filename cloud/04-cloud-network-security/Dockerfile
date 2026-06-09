# Lab 04 — Cloud Network Security
# Provides: cloudmapper + Python 3 (analyze_flows.py)
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      unzip \
      jq \
      git \
      ca-certificates \
      nmap \
    && rm -rf /var/lib/apt/lists/*

# cloudmapper dependencies + cloudmapper itself
# Pin to a known-good commit since cloudmapper hasn't cut a recent release
RUN pip install --no-cache-dir \
      cloudmapper==2.9.1 \
      boto3==1.34.144

# Python stdlib is sufficient for analyze_flows.py — no extra deps needed

WORKDIR /lab
COPY . /lab

CMD ["bash"]
