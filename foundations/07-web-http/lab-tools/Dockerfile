# Tool container for the learner shell (`make shell`) AND the demo (`make demo`,
# which runs demo.py here). Stock python:3.12-slim ships no curl, but this whole
# lab is curl-driven (-v, -c/-b cookie jar, -I) — so add curl while keeping
# Python for demo.py. ca-certificates so HTTPS targets resolve cleanly.
FROM python:3.12-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /lab
