# Module 05 — Posture & Misconfiguration Auditing
# Prowler 4.x + awscli-local for interacting with LocalStack.
FROM python:3.12-slim

# jq (the CLI used by the demo) comes from apt; install it first so a failed
# pip step can't silently leave it out.
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl jq git \
    && rm -rf /var/lib/apt/lists/*

# Pin prowler for reproducibility; let awscli float so pip can pick the build
# whose botocore matches prowler's (pinning awscli==1.33.13 forced botocore==1.34.131
# while prowler 4.3.5 needs botocore==1.34.151 — an unsolvable conflict that left
# prowler uninstalled). No `2>/dev/null`: a resolution failure must fail the build.
RUN pip install --no-cache-dir \
      prowler==4.3.5 \
      awscli-local==0.22.0 \
      awscli

WORKDIR /lab
COPY . /lab

# Prowler 4.x hardcodes the public STS endpoint for credential validation, so it
# can't talk to LocalStack out of the box (it dies on GetCallerIdentity before
# any check runs). Patch it to honour AWS_ENDPOINT_URL. Fails the build loudly
# if the upstream source has drifted from the pinned version.
RUN python3 data/patch-prowler-localstack.py

CMD ["bash"]
