# Lab 04 — Cloud Network Security
# Provides: cloudmapper + Python 3 (analyze_flows.py, check_reachability.py)
# Pinned to 3.9: cloudmapper is unmaintained and its deps don't build on 3.12.
# The bundled Python scripts are all 3.9-compatible.
FROM python:3.9-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      curl \
      unzip \
      jq \
      git \
      ca-certificates \
      nmap \
      build-essential autoconf automake libtool libtool-bin libjq-dev libssl-dev python3-dev \
    && rm -rf /var/lib/apt/lists/*

# cloudmapper is not a pip package — it's cloned and run. Install its requirements
# into /opt/cloudmapper and expose a `cloudmapper` shim. pyjq (in its requirements)
# is why the build toolchain above is needed.
# boto3 + Python stdlib cover demo.py / analyze_flows.py / check_reachability.py.
RUN pip install --no-cache-dir boto3==1.34.144 \
    && git clone --depth 1 https://github.com/duo-labs/cloudmapper.git /opt/cloudmapper \
    && pip install --no-cache-dir -r /opt/cloudmapper/requirements.txt \
    && printf '#!/bin/sh\ncd /opt/cloudmapper && exec python cloudmapper.py "$@"\n' > /usr/local/bin/cloudmapper \
    && chmod +x /usr/local/bin/cloudmapper

WORKDIR /lab
COPY . /lab

CMD ["bash"]
