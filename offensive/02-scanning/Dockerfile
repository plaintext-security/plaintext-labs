FROM python:3.12-slim
RUN apt-get update -qq && apt-get install -y nmap && rm -rf /var/lib/apt/lists/*
WORKDIR /lab
COPY . /lab
