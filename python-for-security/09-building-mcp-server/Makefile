.PHONY: up down reset demo shell refresh

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec mcp-server bash

refresh:   ## Re-fetch the LIVE abuse.ch feeds via shared cache (needs MB_AUTH_KEY) into feeds/db.json
	. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh" && fetch_feed feodo-ipblocklist feeds/feodo.json && fetch_feed urlhaus-recent feeds/urlhaus.csv && docker compose run --rm -e FEODO_FILE=feeds/feodo.json -e URLHAUS_FILE=feeds/urlhaus.csv mcp-server python feeds/fetch_feeds.py && rm -f feeds/feodo.json feeds/urlhaus.csv

demo:      ## Start server and make three test tool calls (against real abuse.ch IOCs)
	docker compose run --rm mcp-server sh -c '\
		echo "=== enrich_ip: real malicious C2 IP (Feodo Tracker) ==="; \
		python test_call.py enrich_ip "{\"ip\": \"162.243.103.246\"}"; \
		echo; \
		echo "=== enrich_ip: clean IP (public resolver) ==="; \
		python test_call.py enrich_ip "{\"ip\": \"8.8.8.8\"}"; \
		echo; \
		echo "=== enrich_ip: unknown IP (404, not in feed) ==="; \
		python test_call.py enrich_ip "{\"ip\": \"192.0.2.200\"}"; \
		echo; \
		echo "=== enrich_ip: invalid format ==="; \
		python test_call.py enrich_ip "{\"ip\": \"not-an-ip\"}"'
