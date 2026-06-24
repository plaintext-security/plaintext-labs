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

fetch:     ## (needs network) pull real Suricata eve.json alerts (shared cache) into data/alerts.json
	. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh" && fetch_file suricata-wrccdc-2018-alerts data/alerts.json && printf 'Suricata eve.json alerts from WRCCDC-2018 PCAP, via FrankHassanabad/suricata-sample-data\nSource URL: https://raw.githubusercontent.com/FrankHassanabad/suricata-sample-data/master/samples/wrccdc-2018/alerts-only.json\nRetrieved: %s (via shared dataset cache)\n' "$$(date +%Y-%m-%d)" > data/PROVENANCE.txt && echo "Wrote real Suricata alerts to data/alerts.json; provenance in data/PROVENANCE.txt."
