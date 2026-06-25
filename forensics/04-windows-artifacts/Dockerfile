FROM python:3.12-slim

# Install chainsaw (Rust binary) and python-registry
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install chainsaw (pre-built release binary). Chainsaw ships gnu (not musl)
# builds and now publishes both x86_64 and aarch64 Linux assets, so this works
# on amd64 (CI) and arm64 alike.
RUN CHAINSAW_VERSION=2.16.0 && \
    ARCH="$(uname -m)" && \
    curl -fsSL "https://github.com/WithSecureLabs/chainsaw/releases/download/v${CHAINSAW_VERSION}/chainsaw_${ARCH}-unknown-linux-gnu.tar.gz" \
    | tar -xz -C /usr/local/bin/ --strip-components=1 chainsaw/chainsaw && \
    chmod +x /usr/local/bin/chainsaw

# Install python-registry and python-evtx
RUN pip install --no-cache-dir python-registry==1.3.1

WORKDIR /lab
COPY . /lab/
