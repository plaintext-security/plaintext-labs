# Module 06 — Infrastructure-as-Code Security
# checkov + tfsec + trivy, all pinned for reproducibility.
FROM python:3.12-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl git jq unzip \
    && rm -rf /var/lib/apt/lists/*

# checkov — Bridgecrew/PAN IaC scanner
RUN pip install --no-cache-dir checkov==3.2.270

# tfsec — Aqua Terraform scanner
RUN curl -sSfL \
      "https://github.com/aquasecurity/tfsec/releases/download/v1.28.6/tfsec-linux-amd64" \
      -o /usr/local/bin/tfsec && chmod +x /usr/local/bin/tfsec

# trivy — Aqua all-in-one scanner (config + container)
RUN curl -sSfL \
      "https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh" \
      | sh -s -- -b /usr/local/bin v0.52.2

WORKDIR /lab
COPY . /lab

CMD ["bash"]
