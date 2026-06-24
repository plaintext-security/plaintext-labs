.PHONY: up down reset demo shell fetch

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

demo:      ## Run report.py over data/alerts.json
	docker compose run --rm lab python report.py

fetch:     ## (needs network) pull real Suricata eve.json alerts into data/alerts.json
	docker compose run --rm lab python data/fetch_alerts.py
