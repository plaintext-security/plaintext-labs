.PHONY: up down reset demo shell refresh

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec mcp-server bash

refresh:   ## Re-fetch the LIVE abuse.ch feeds (Feodo Tracker + URLhaus) into feeds/db.json
	docker compose run --rm mcp-server python feeds/fetch_feeds.py

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
