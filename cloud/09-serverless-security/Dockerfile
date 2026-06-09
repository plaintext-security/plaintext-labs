# Module 09 — Serverless Security
# AWS SAM CLI + cloudfox + awscli-local, pinned versions.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl git jq unzip zip wget \
    && rm -rf /var/lib/apt/lists/*

# AWS SAM CLI
RUN curl -sSfL \
      "https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip" \
      -o /tmp/sam.zip \
    && unzip -q /tmp/sam.zip -d /tmp/sam-install \
    && /tmp/sam-install/install \
    && rm -rf /tmp/sam.zip /tmp/sam-install

# awscli v2 + awslocal wrapper
RUN pip install --no-cache-dir \
      awscli-local==0.22.0 \
      awscli==1.33.13

# cloudfox — Lambda permission enumeration
RUN curl -sSfL \
      "https://github.com/BishopFox/cloudfox/releases/download/v1.14.2/cloudfox-linux-amd64.zip" \
      -o /tmp/cloudfox.zip \
    && unzip -q /tmp/cloudfox.zip -d /tmp/cloudfox \
    && mv /tmp/cloudfox/cloudfox /usr/local/bin/cloudfox \
    && chmod +x /usr/local/bin/cloudfox \
    && rm -rf /tmp/cloudfox.zip /tmp/cloudfox

WORKDIR /lab
COPY . /lab

CMD ["bash"]
