FROM python:3.12-slim

# subprocess/shlex are stdlib; no extra deps. (The learner wraps real tools like
# nmap/whois; the demo uses `echo` so the injection is safe to show in CI.)
WORKDIR /lab
COPY . /lab

CMD ["sleep", "infinity"]
