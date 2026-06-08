FROM debian:12-slim
RUN apt-get update -qq && apt-get install -y --no-install-recommends \
        gcc gdb python3 libc6-dev binutils file && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /lab
COPY . /lab
