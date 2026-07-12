FROM python:3.12-slim

RUN pip install --no-cache-dir "typer==0.15.*" "fastapi==0.115.*" "httpx==0.27.*"

WORKDIR /lab
COPY . /lab

CMD ["sleep", "infinity"]
