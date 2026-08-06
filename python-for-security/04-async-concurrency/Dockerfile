FROM python:3.12-slim

RUN pip install --no-cache-dir "httpx==0.27.*" "pydantic==2.*"

WORKDIR /lab
COPY . /lab

CMD ["sleep", "infinity"]
