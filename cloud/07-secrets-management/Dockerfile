# Module 07 — Secrets Management & Detection
# trufflehog + vault CLI, pinned versions.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl git jq unzip wget \
    && rm -rf /var/lib/apt/lists/*

# trufflehog — secrets scanner
RUN curl -sSfL \
      "https://github.com/trufflesecurity/trufflehog/releases/download/v3.79.0/trufflehog_3.79.0_linux_amd64.tar.gz" \
      | tar -xz -C /usr/local/bin trufflehog && chmod +x /usr/local/bin/trufflehog

# vault CLI (for interacting with the Vault container)
RUN curl -sSfL \
      "https://releases.hashicorp.com/vault/1.17.2/vault_1.17.2_linux_amd64.zip" \
      -o /tmp/vault.zip \
    && unzip /tmp/vault.zip -d /usr/local/bin \
    && rm /tmp/vault.zip

# gitleaks — for the stretch/comparison exercise
RUN curl -sSfL \
      "https://github.com/gitleaks/gitleaks/releases/download/v8.18.4/gitleaks_8.18.4_linux_x64.tar.gz" \
      | tar -xz -C /usr/local/bin gitleaks

WORKDIR /lab
COPY . /lab

CMD ["bash"]
