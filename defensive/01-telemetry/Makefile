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
	curl -fsSL https://raw.githubusercontent.com/logpai/loghub/master/OpenSSH/OpenSSH_2k.log -o data/OpenSSH_2k.log
	@echo "Fetched data/OpenSSH_2k.log — pipeline.py will now consume the real log. See data/PROVENANCE.md."
