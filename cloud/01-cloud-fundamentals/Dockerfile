# Lab 01 — Cloud Fundamentals & Shared Responsibility
# Provides: awscli v2 + awslocal (thin LocalStack wrapper) + Python 3
FROM python:3.12-slim

# aws-cli v2 is not on PyPI; install the official binary bundle.
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      unzip \
      groff \
      less \
      jq \
    && rm -rf /var/lib/apt/lists/*

# Install AWS CLI v2 (official binary, pinned version)
ARG AWSCLI_VERSION=2.17.20
RUN curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64-${AWSCLI_VERSION}.zip" \
      -o /tmp/awscliv2.zip \
    && unzip /tmp/awscliv2.zip -d /tmp \
    && /tmp/aws/install \
    && rm -rf /tmp/awscliv2.zip /tmp/aws

# localstack Python tools: awslocal wraps `aws` to point at LocalStack
RUN pip install --no-cache-dir awscli-local==0.22.0

# Fake credentials so awslocal doesn't complain (LocalStack ignores them)
ENV AWS_ACCESS_KEY_ID=test \
    AWS_SECRET_ACCESS_KEY=test \
    AWS_DEFAULT_REGION=us-east-1

WORKDIR /lab
COPY . /lab

CMD ["bash"]
