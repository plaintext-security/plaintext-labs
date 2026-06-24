# Module 01 — Telemetry lab.
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
	docker compose run --rm lab python3 pipeline.py
fetch-data: ## Pull the real loghub OpenSSH_2k.log (2000 lines, host "LabSZ") into data/
	. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh" && \
	fetch_file loghub-openssh data/OpenSSH_2k.log
	@echo "Fetched data/OpenSSH_2k.log — pipeline.py will now consume the real log. See data/PROVENANCE.md."
