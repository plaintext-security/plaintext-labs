FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install hindsight
RUN pip install --no-cache-dir pyhindsight==20250307

WORKDIR /lab
COPY . /lab/
