.PHONY: up down reset shell demo gen

up:
	docker compose up -d --build

# Regenerate data/eve.json from the real anchor PCAP via Suricata (ET Open).
# Runs on the HOST (needs Docker; the lab container has Python, not Suricata).
# See PROVENANCE.md; the PCAP is fetched + checksum-verified, never mirrored.
gen:
	./gen_eve.sh

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

# Reference demo: STREAM the real Suricata eve.json (flat memory, replayed to ~175k
# events), answer triage questions with a duckdb columnar query over real EVE fields,
# and emit structlog JSON events.
demo:
	docker compose run --rm lab python demo.py
