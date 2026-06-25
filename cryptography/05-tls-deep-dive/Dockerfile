# Module 05 — TLS Deep Dive (testssl.sh scanner)
FROM debian:12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      openssl \
      curl \
      wget \
      git \
      ca-certificates \
      bsdextrautils \
      procps \
      dnsutils \
      grep \
      less \
      bash \
    && rm -rf /var/lib/apt/lists/*

# Install testssl.sh (pinned to the 3.2 release branch)
RUN git clone --depth 1 --branch 3.2 https://github.com/drwetter/testssl.sh.git /opt/testssl && \
    ln -s /opt/testssl/testssl.sh /usr/local/bin/testssl.sh

WORKDIR /lab
COPY . /lab

CMD ["bash"]
