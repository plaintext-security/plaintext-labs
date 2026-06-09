# Module 05 — Posture & Misconfiguration Auditing
# Prowler 4.x + awscli-local for interacting with LocalStack.
FROM python:3.12-slim

# Pin versions for reproducibility
RUN pip install --no-cache-dir \
      prowler==4.3.5 \
      awscli-local==0.22.0 \
      awscli==1.33.13 \
      jq==1.6.0 2>/dev/null; \
    apt-get update && apt-get install -y --no-install-recommends \
      curl jq git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /lab
COPY . /lab

CMD ["bash"]
