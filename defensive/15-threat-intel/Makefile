# Module 15 — Threat Intelligence lab.
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
	docker compose run --rm lab python enrich.py --demo

# Pull TODAY's live abuse.ch ThreatFox recent-IOC export → data/threatfox_recent.csv
# (see data/PROVENANCE.md). enrich.py prefers this live feed and falls back to the
# committed snapshot when it is absent. NOT run in CI — you run it locally.
THREATFOX_CSV ?= https://threatfox.abuse.ch/export/csv/recent/
fetch-data: ## Download the live ThreatFox recent-IOC CSV → data/threatfox_recent.csv
	@echo "Fetching $(THREATFOX_CSV) ..."
	curl -fsSL "$(THREATFOX_CSV)" -o data/threatfox_recent.csv
	@echo "Done. data/threatfox_recent.csv holds today's REAL IOCs — enrich with: python enrich.py <indicator>"
