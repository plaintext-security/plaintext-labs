# Lab 03 — IAM Attack Paths
# Provides: Python 3 (analyze.py) + awscli + awslocal + pmapper
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      unzip \
      jq \
      git \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# AWS CLI v2
ARG AWSCLI_VERSION=2.17.20
RUN curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64-${AWSCLI_VERSION}.zip" \
      -o /tmp/awscliv2.zip \
    && unzip /tmp/awscliv2.zip -d /tmp \
    && /tmp/aws/install \
    && rm -rf /tmp/awscliv2.zip /tmp/aws

# awslocal + boto3 + principal-mapper (pmapper)
RUN pip install --no-cache-dir \
      awscli-local==0.22.0 \
      boto3==1.34.144 \
      principalmapper==1.1.5

# AWS credential stubs for LocalStack
ENV AWS_ACCESS_KEY_ID=test \
    AWS_SECRET_ACCESS_KEY=test \
    AWS_DEFAULT_REGION=us-east-1

RUN mkdir -p /root/.aws && printf \
      "[profile localstack]\nregion = us-east-1\noutput = json\n" \
      >> /root/.aws/config \
    && printf \
      "[localstack]\naws_access_key_id = test\naws_secret_access_key = test\n" \
      >> /root/.aws/credentials

WORKDIR /lab
COPY . /lab

CMD ["bash"]
