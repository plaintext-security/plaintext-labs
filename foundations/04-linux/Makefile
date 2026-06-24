.PHONY: up down reset shell demo fetch-data

# Download the real public SSH auth log (loghub OpenSSH dataset) into data/ via the
# shared dataset cache (lib/fetch.sh) — downloaded ONCE, reused across every lab.
# Provenance: github.com/logpai/loghub — OpenSSH_2k.log, a 2,000-line excerpt of a
# real internet-facing sshd's log (655k lines total, see data/PROVENANCE.md).
# NOTE (runner-validation): this target hits the network; it has not been run in
# this environment. Validate `make fetch-data && make demo` on a Linux runner.
fetch-data:
	@. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh"; \
		fetch_file loghub-openssh data/OpenSSH_2k.log
	@echo "Fetched real loghub OpenSSH log -> data/OpenSSH_2k.log"

up: fetch-data
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose run --rm lab bash

# Show expected triage output (users, SUID, processes, log analysis)
demo:
	docker compose run --rm lab python3 demo.py
