# Lab 02 — Cloud Identity & IAM
# Provides: cloudfox (pre-built binary) + awscli v2 + awslocal + boto3
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      unzip \
      jq \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# AWS CLI v2
ARG AWSCLI_VERSION=2.17.20
RUN curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64-${AWSCLI_VERSION}.zip" \
      -o /tmp/awscliv2.zip \
    && unzip /tmp/awscliv2.zip -d /tmp \
    && /tmp/aws/install \
    && rm -rf /tmp/awscliv2.zip /tmp/aws

# awslocal (points `aws` calls at LocalStack)
RUN pip install --no-cache-dir awscli-local==0.22.0 boto3==1.34.144

# cloudfox — BishopFox's cloud enumeration tool (pre-built Linux binary)
ARG CLOUDFOX_VERSION=1.14.0
RUN curl -fsSL \
      "https://github.com/BishopFox/cloudfox/releases/download/v${CLOUDFOX_VERSION}/cloudfox-linux-amd64.zip" \
      -o /tmp/cloudfox.zip \
    && unzip /tmp/cloudfox.zip -d /usr/local/bin \
    && chmod +x /usr/local/bin/cloudfox \
    && rm /tmp/cloudfox.zip

# AWS credentials for LocalStack (ignored by LocalStack, but required by the CLI)
ENV AWS_ACCESS_KEY_ID=test \
    AWS_SECRET_ACCESS_KEY=test \
    AWS_DEFAULT_REGION=us-east-1

# Configure a named profile so cloudfox --profile localstack works
RUN mkdir -p /root/.aws && printf \
      "[profile localstack]\nregion = us-east-1\noutput = json\n" \
      >> /root/.aws/config \
    && printf \
      "[localstack]\naws_access_key_id = test\naws_secret_access_key = test\n" \
      >> /root/.aws/credentials

WORKDIR /lab
COPY . /lab

CMD ["bash"]
