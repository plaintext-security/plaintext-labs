FROM python:3.12-slim
RUN apt-get update -qq && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        xxd jq curl coreutils \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /lab
COPY data/ data/
COPY demo.py .
