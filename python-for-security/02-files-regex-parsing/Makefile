.PHONY: up down reset demo shell fetch

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

fetch:     ## (needs network) pull the full 2,000-line loghub OpenSSH corpus (shared cache) into data/sshd.log
	. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh" && fetch_file loghub-openssh data/sshd.log && printf 'Source: loghub OpenSSH_2k.log (real internet-facing SSH server '\''LabSZ'\'')\nURL: https://raw.githubusercontent.com/logpai/loghub/master/OpenSSH/OpenSSH_2k.log\nRetrieved: %s (full 2,000-line corpus via shared dataset cache)\nLicense/terms: loghub research dataset, see https://github.com/logpai/loghub\n' "$$(date +%Y-%m-%d)" > data/PROVENANCE.txt && echo "Wrote full loghub OpenSSH corpus to data/sshd.log; provenance in data/PROVENANCE.txt."

demo:      ## Run the reference parser and show top offending IPs
	@# data/sshd.log is gitignored (real log), so ensure it exists (shared cache) before parsing.
	@[ -s data/sshd.log ] || $(MAKE) fetch
	docker compose run --rm lab python parse_log.py
