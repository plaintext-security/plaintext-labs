# Module 05 — Browser & Application Artifacts lab.
# Standard targets: up / down / reset / demo / shell / fetch-data
.PHONY: up down reset demo shell fetch-data

# Real public dataset: Digital Corpora "Nitroba University Harassment" scenario PCAP.
# Browser/webmail artifacts (webmail sessions, user-agents) are reconstructed from the capture.
# Pulled from the shared dataset cache (lib/fetch.sh, source name digitalcorpora-nitroba).
# See PROVENANCE.md for dataset details and SHA-256 placeholder.

up:  ## Build and start the hindsight + sqlite3 container
	docker compose up -d --build

fetch-data:  ## Download the real Nitroba scenario PCAP into data/ (idempotent, ~60MB)
	@mkdir -p data
	@if [ -f data/nitroba.pcap ]; then \
		echo "exists: data/nitroba.pcap"; \
	else \
		echo "fetch:  data/nitroba.pcap (~60MB)"; \
		. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh"; \
		fetch_file digitalcorpora-nitroba data/nitroba.pcap; \
	fi
	@echo "Done. Verify SHA-256 against PROVENANCE.md. The bundled data/History (Chrome SQLite)"
	@echo "remains the offline demo seed; nitroba.pcap is the real artifact for webmail reconstruction."

down:  ## Stop and remove the container
	docker compose down

reset:  ## Tear down completely
	docker compose down --rmi local --volumes --remove-orphans

shell:  ## Open a shell in the lab container
	docker compose exec lab bash

demo:  ## Extract Chrome browser artifacts from data/History and display findings
	docker compose run --rm lab sh -c '\
		echo "=== Module 05 — Browser & Application Artifacts: worked demo ==="; \
		echo; \
		echo "-- Visited URLs (incident window 2024-03-15 02:00–02:35 UTC) --"; \
		sqlite3 data/History \
			"SELECT datetime(last_visit_time/1000000 - 11644473600, '"'"'unixepoch'"'"') as visited_at, \
			        url, visit_count \
			 FROM urls \
			 WHERE last_visit_time/1000000 - 11644473600 BETWEEN 1710468000 AND 1710470100 \
			 ORDER BY last_visit_time;"; \
		echo; \
		echo "-- Downloads --"; \
		sqlite3 data/History \
			"SELECT datetime(start_time/1000000 - 11644473600, '"'"'unixepoch'"'"') as dl_at, \
			        target_path, tab_url, total_bytes \
			 FROM downloads ORDER BY start_time;"; \
		echo; \
		echo "-- Search Terms --"; \
		sqlite3 data/History \
			"SELECT k.term, datetime(u.last_visit_time/1000000 - 11644473600, '"'"'unixepoch'"'"') \
			 FROM keyword_search_terms k JOIN urls u ON k.url_id = u.id \
			 ORDER BY u.last_visit_time;"; \
		echo; \
		echo "-- All URLs (full history) --"; \
		sqlite3 data/History \
			"SELECT datetime(last_visit_time/1000000 - 11644473600, '"'"'unixepoch'"'"'), url \
			 FROM urls ORDER BY last_visit_time;"; \
		echo; \
		echo "=== KEY FINDINGS ==="; \
		echo "  - Google searches for anonymous/untraceable email and IP hiding"; \
		echo "  - Visit to willselfdestruct.com and sendanonymousemail.net (anonymizer webmail)"; \
		echo "  - Download of anon_mailer.exe from pastebin.com"; \
		echo "  - Gmail Sent-folder activity in the harassment window"; \
		echo "=== Demo complete. ==="'
