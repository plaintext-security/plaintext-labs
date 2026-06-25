FROM python:3.12.9-slim

WORKDIR /lab

RUN pip install --no-cache-dir \
    sigma-cli==3.0.2 \
    pySigma-backend-splunk==2.1.0 \
    pySigma-pipeline-sysmon==2.0.0 \
    pytest==8.3.5 \
    pyyaml==6.0.3

COPY . /lab

CMD ["sleep", "infinity"]
