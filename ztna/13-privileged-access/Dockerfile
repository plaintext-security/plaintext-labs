# Module 13 — Privileged Access (Teleport Community Edition)
# One image used for every service in the lab: it carries the Teleport binaries
# (teleport, tctl, tsh) copied out of the official upstream image, plus bash,
# openssh-client, curl, jq, and netcat — so the auth/proxy service, the node,
# the bootstrap step, and the operator's client shell all run from the same
# place and stay legible.
#
# The Teleport binaries are copied out of the official upstream image; the
# runtime is plain debian-slim so we have bash/curl/jq/nc for the workload and
# bootstrap scripts (the upstream image alone has no shell to run those in).
FROM public.ecr.aws/gravitational/teleport:18.10.0 AS teleport

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
      bash curl jq ca-certificates openssh-client netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY --from=teleport /usr/local/bin/teleport /usr/local/bin/teleport
COPY --from=teleport /usr/local/bin/tctl     /usr/local/bin/tctl
COPY --from=teleport /usr/local/bin/tsh      /usr/local/bin/tsh

WORKDIR /opt/teleport
CMD ["bash"]
