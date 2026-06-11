# Module 07 — Secrets Management & Detection
# trufflehog + vault CLI, pinned versions.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl git jq unzip wget postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python clients for the runtime-fetch app + the AWS Secrets Manager variant:
#   hvac          — the official Vault API client (an app fetches its secret at runtime)
#   psycopg2      — connect to Postgres with the dynamic credential Vault minted
#   awscli        — the `aws` CLI (provides the binary awslocal wraps)
#   awscli-local  — `awslocal` targets the LocalStack container
RUN pip install --no-cache-dir \
      hvac==2.3.0 psycopg2-binary==2.9.9 awscli==1.33.44 awscli-local==0.22.0

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
