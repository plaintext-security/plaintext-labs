FROM debian:12-slim
RUN apt-get update -qq && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        openssl python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /lab
COPY demo.py .
