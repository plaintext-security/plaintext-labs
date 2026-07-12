FROM python:3.12-slim

RUN pip install --no-cache-dir "pydantic==2.*" "pydantic-settings==2.*"

WORKDIR /lab
COPY . /lab

CMD ["sleep", "infinity"]
