# Module 08 — CI/CD Pipeline Security
# gitleaks + trivy, pinned versions.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl git jq \
    && rm -rf /var/lib/apt/lists/*

# gitleaks — fast secrets scanner, offline CI gate
RUN curl -sSfL \
      "https://github.com/gitleaks/gitleaks/releases/download/v8.18.4/gitleaks_8.18.4_linux_x64.tar.gz" \
      | tar -xz -C /usr/local/bin gitleaks

# trivy — vulnerability and misconfiguration scanner
RUN curl -sSfL \
      "https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh" \
      | sh -s -- -b /usr/local/bin v0.52.2

WORKDIR /lab
COPY . /lab

CMD ["bash"]
