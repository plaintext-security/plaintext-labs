# Module 09 — Email Authentication
# bind9 DNS (seeded) + dig + Python dnspython
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      bind9 \
      bind9utils \
      dnsutils \
      openssl \
      curl \
      jq \
      less \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir dnspython==2.7.0

# Configure local bind9 with corp-fictional.com zone
COPY data/named.conf /etc/bind/named.conf.local
COPY data/corp-fictional.zone /etc/bind/corp-fictional.zone

WORKDIR /lab
COPY . /lab

CMD ["/bin/bash", "-c", "named -f -u bind & sleep 2 && bash"]
