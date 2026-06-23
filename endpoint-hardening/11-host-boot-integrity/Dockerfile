# Module 11 — Host & Boot Integrity
# A minimal Debian host with AIDE (Advanced Intrusion Detection Environment) installed.
# The container stands in for "a host you've just provisioned": you baseline its
# filesystem, plant a tamper, and prove AIDE's known-good comparison catches it.
#
# We pin aide from Debian stable. The watched tree, the AIDE config, and the
# baseline/tamper scripts are mounted in at runtime so the learner can edit them.
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
      aide aide-common cron coreutils findutils procps \
    && rm -rf /var/lib/apt/lists/*

# A small "application" tree the lab watches — a binary, a config, and a web root.
# Kept legible so a planted change is obvious in the AIDE report.
RUN mkdir -p /srv/app/bin /srv/app/etc /srv/app/www /etc/cron.d \
    && printf '#!/bin/sh\necho "meridian-app v1.0"\n' > /srv/app/bin/meridian \
    && chmod 0755 /srv/app/bin/meridian \
    && printf 'listen=8080\nlog_level=info\n' > /srv/app/etc/app.conf \
    && printf '<h1>Meridian</h1>\n' > /srv/app/www/index.html \
    && chmod 0644 /srv/app/etc/app.conf /srv/app/www/index.html

WORKDIR /lab
COPY . /lab

CMD ["sleep", "infinity"]
