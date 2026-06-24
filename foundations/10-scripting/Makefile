.PHONY: up down reset shell demo fetch-data

# Download the SAME real public SSH brute-force log used in module 04
# (loghub OpenSSH dataset) into data/ via the shared dataset cache (lib/fetch.sh) —
# so it is reused from cache, not re-downloaded. Provenance: github.com/logpai/loghub —
# OpenSSH_2k.log, a 2,000-line excerpt of a real internet-facing sshd's log.
# See data/PROVENANCE.md.
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

# Shell with your current directory mounted — write topips.py here and it persists
shell:
	docker compose run --rm lab bash

# Show expected output + Python building blocks for topips.py
demo:
	docker compose run --rm lab python3 demo.py
