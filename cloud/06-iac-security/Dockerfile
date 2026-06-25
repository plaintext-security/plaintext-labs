# Module 06 — Infrastructure-as-Code Security
# checkov + tfsec + trivy, all pinned for reproducibility.
FROM python:3.12-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl git jq unzip \
    && rm -rf /var/lib/apt/lists/*

# Resolve the build arch (amd64 / arm64) so the pinned binaries below are
# fetched for the host we are actually running on (CI is amd64; Apple Silicon
# is arm64). Without this the hard-coded *-amd64 asset would be emulated or
# fail to execute on arm64.
ARG TARGETARCH

# checkov — Bridgecrew/PAN IaC scanner
RUN pip install --no-cache-dir checkov==3.2.270

# tfsec — Aqua Terraform scanner (asset names use linux-amd64 / linux-arm64)
RUN curl -sSfL \
      "https://github.com/aquasecurity/tfsec/releases/download/v1.28.6/tfsec-linux-${TARGETARCH}" \
      -o /usr/local/bin/tfsec && chmod +x /usr/local/bin/tfsec

# trivy — Aqua all-in-one scanner (config + container). v0.52.2 was retracted
# upstream (the tag resolves but the release asset 404s), so this is re-pinned
# to a current stable release.
RUN curl -sSfL \
      "https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh" \
      | sh -s -- -b /usr/local/bin v0.71.2

WORKDIR /lab
COPY . /lab

CMD ["bash"]
