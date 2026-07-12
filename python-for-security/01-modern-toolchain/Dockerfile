FROM python:3.12-slim

# The modern toolchain the module standardizes on. uv and ruff are standalone,
# offline-friendly binaries (no node needed); pyright is added by the learner as
# part of the full gate (it fetches a node runtime on first run).
RUN pip install --no-cache-dir uv==0.5.* ruff==0.8.*

WORKDIR /lab
COPY . /lab

CMD ["sleep", "infinity"]
