# Module 03 — Linux Telemetry lab.
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
	docker compose run --rm lab python3 demo.py
fetch-data: ## Pull the real loghub Linux_2k.log (genuine syslog, host "combo") into data/
	curl -fsSL https://raw.githubusercontent.com/logpai/loghub/master/Linux/Linux_2k.log -o data/Linux_2k.log
	@echo "Fetched data/Linux_2k.log — a real Linux syslog. See data/PROVENANCE.md for how to"
	@echo "generate genuine auditd telemetry from an Atomic Red Team test."
