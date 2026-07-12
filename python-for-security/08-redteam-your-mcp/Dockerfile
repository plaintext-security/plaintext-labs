FROM python:3.12-slim

# Offline red-team demo: no model call needed to show indirect prompt injection
# and the regression guard that catches it. pytest runs the regression gate.
RUN pip install --no-cache-dir "pytest==8.*"

WORKDIR /lab
COPY . /lab

CMD ["sleep", "infinity"]
