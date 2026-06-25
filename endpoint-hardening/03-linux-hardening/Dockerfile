# Module 03 — Linux Hardening to CIS
# Lynis + OpenSCAP + SCAP Security Guide (SSG) on Ubuntu 22.04
FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ARG LYNIS_VERSION=3.1.1
# SCAP Security Guide content (the ssg-ubuntu2204 datastream) is NOT packaged in
# Ubuntu 22.04 — only Debian ships ssg-*. We fetch it from the upstream
# ComplianceAsCode/content GitHub release instead (the canonical SSG source).
ARG SSG_VERSION=0.1.73

# The OpenSCAP scanner (the `oscap` binary) ships in Ubuntu's "universe"
# component as libopenscap8 (there is no openscap-scanner/openscap-utils package
# on Ubuntu). universe is not enabled in the minimal ubuntu:22.04 base image.
RUN sed -i 's/ main restricted$/ main restricted universe/' /etc/apt/sources.list

RUN apt-get update && apt-get install -y --no-install-recommends \
      libopenscap8 \
      unzip \
      wget \
      curl \
      python3 \
      python3-pip \
      procps \
      net-tools \
      less \
      jq \
    && rm -rf /var/lib/apt/lists/*

# Stage the SCAP Security Guide Ubuntu 22.04 datastream where oscap expects it.
RUN curl -fsSL \
      "https://github.com/ComplianceAsCode/content/releases/download/v${SSG_VERSION}/scap-security-guide-${SSG_VERSION}.zip" \
      -o /tmp/ssg.zip \
    && unzip -q /tmp/ssg.zip -d /tmp/ssg \
    && mkdir -p /usr/share/xml/scap/ssg/content \
    && cp /tmp/ssg/scap-security-guide-${SSG_VERSION}/ssg-ubuntu2204-ds.xml \
          /usr/share/xml/scap/ssg/content/ \
    && rm -rf /tmp/ssg.zip /tmp/ssg

# Install Lynis from the CISOfy repository for the pinned version
RUN wget -q "https://github.com/CISOfy/lynis/archive/refs/tags/${LYNIS_VERSION}.tar.gz" \
      -O /tmp/lynis.tar.gz \
    && tar -xzf /tmp/lynis.tar.gz -C /opt \
    && mv /opt/lynis-${LYNIS_VERSION} /opt/lynis \
    && ln -s /opt/lynis/lynis /usr/local/bin/lynis \
    && rm /tmp/lynis.tar.gz

WORKDIR /lab
COPY . /lab

CMD ["bash"]
