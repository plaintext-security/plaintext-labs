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

demo:      ## Run full MISP workflow: create event, add IOCs, enrich, tag, publish
	docker compose run --rm lab python workflow.py
