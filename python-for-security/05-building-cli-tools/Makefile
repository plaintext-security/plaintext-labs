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

demo:      ## Show ioc-check --help and a sample enrich run
	docker compose run --rm lab sh -c '\
		echo "=== ioc-check --help ==="; \
		python ioc-check.py --help; \
		echo; \
		echo "=== ioc-check enrich --ioc 8.8.8.8 ==="; \
		python ioc-check.py enrich --ioc 8.8.8.8; \
		echo; \
		echo "=== ioc-check enrich --ioc not-valid (should exit 1) ==="; \
		python ioc-check.py enrich --ioc not-valid || true'
