FROM python:3.12-slim

RUN pip install --no-cache-dir "polars==1.*" "duckdb==1.*" "structlog==24.*"

WORKDIR /lab
COPY . /lab

CMD ["sleep", "infinity"]
