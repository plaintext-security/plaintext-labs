FROM python:3.12-slim

# pydantic parses the driven dissector's structured output (Suricata EVE JSON) into a
# typed union. subprocess/ipaddress are stdlib. The learner wraps real tools like
# nmap/whois/suricata; the demo uses `echo` so the injection is safe to show in CI, and
# ships a recorded eve.json so Suricata itself is not needed offline.
RUN pip install --no-cache-dir "pydantic==2.*"

WORKDIR /lab
COPY . /lab

CMD ["sleep", "infinity"]
