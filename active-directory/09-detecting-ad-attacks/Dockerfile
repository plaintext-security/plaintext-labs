FROM debian:bookworm-slim

ARG DEBIAN_FRONTEND=noninteractive
ARG CHAINSAW_VERSION=2.10.0

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install chainsaw
RUN curl -sSfL \
    "https://github.com/WithSecureLabs/chainsaw/releases/download/v${CHAINSAW_VERSION}/chainsaw_x86_64-unknown-linux-gnu.tar.gz" \
    -o /tmp/chainsaw.tar.gz && \
    tar -xzf /tmp/chainsaw.tar.gz -C /usr/local/bin --strip-components=1 chainsaw/chainsaw && \
    chmod +x /usr/local/bin/chainsaw && \
    rm /tmp/chainsaw.tar.gz

# Install sigma-cli for rule validation
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir sigma-cli pySigma-backend-elasticsearch

WORKDIR /lab
COPY data /lab/data
COPY scripts /lab/scripts
