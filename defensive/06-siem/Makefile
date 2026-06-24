.PHONY: up down reset shell demo fetch-data
up:
	docker compose up -d --build
down:
	docker compose down
reset:
	docker compose down --rmi local --volumes --remove-orphans
shell:
	docker compose exec lab bash
demo:
	docker compose run --rm lab python3 siem.py

# Fetch a real public sshd log (loghub OpenSSH_2k.log) so you can run the
# ingest/normalize path on genuine raw auth lines, not just the curated seed.
# See data/PROVENANCE.md. Not run in CI — you run it locally.
SSH_LOG_URL ?= https://raw.githubusercontent.com/logpai/loghub/master/OpenSSH/OpenSSH_2k.log
fetch-data: ## Download the real loghub OpenSSH_2k.log → data/raw/OpenSSH_2k.log
	@mkdir -p data/raw
	@echo "Downloading $(SSH_LOG_URL) ..."
	curl -fL -o data/raw/OpenSSH_2k.log "$(SSH_LOG_URL)"
	@echo "Done. Real sshd auth lines are in data/raw/OpenSSH_2k.log."
	@echo "Extend normalize() in siem.py to ingest them into the events table."
