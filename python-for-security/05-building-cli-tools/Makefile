.PHONY: up down reset demo shell refresh

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

refresh:   ## Re-fetch the LIVE abuse.ch feeds via shared cache (needs MB_AUTH_KEY) into feeds/db.json
	. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh" && fetch_feed feodo-ipblocklist feeds/feodo.json && fetch_feed urlhaus-recent feeds/urlhaus.csv && docker compose run --rm -e FEODO_FILE=feeds/feodo.json -e URLHAUS_FILE=feeds/urlhaus.csv lab python feeds/fetch_feeds.py && rm -f feeds/feodo.json feeds/urlhaus.csv

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
