.PHONY: up down reset demo shell refresh

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

refresh:   ## Re-fetch the LIVE abuse.ch feeds (Feodo Tracker + URLhaus) into feeds/db.json
	docker compose run --rm lab python feeds/fetch_feeds.py

demo:      ## Run enrich.py against the real-feed-backed API and show enriched output
	docker compose run --rm lab python enrich.py
