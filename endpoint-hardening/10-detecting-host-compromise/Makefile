# Module 10 — Detecting Host Compromise
# Standard targets: up / down / reset / demo / shell  (+ fetch / convert)

.PHONY: up down reset demo shell fetch convert

# Stage the real EVTX-ATTACK-SAMPLES (3 phases) from the shared cache (host side).
fetch:
	sh fetch-data.sh

up: fetch
	docker compose up -d --build
	@$(MAKE) -s convert

# Render the staged real EVTX into data/events.json via evtx_dump.py + evtx_to_json.py.
convert:
	docker compose exec lab bash -c 'set -e; \
	  : > /lab/data/events.json.tmp; \
	  for f in /lab/data/evtx/*.evtx; do \
	    phase=$$(basename "$$f" | cut -d_ -f1); \
	    evtx_dump.py "$$f" 2>/dev/null | python3 /lab/evtx_to_json.py --phase "$$phase" --source "$$(basename $$f)" >> /lab/data/events.json.tmp; \
	  done; \
	  python3 -c "import json,sys; recs=[json.loads(l) for l in open(\"/lab/data/events.json.tmp\") if l.strip()]; json.dump(recs, open(\"/lab/data/events.json\",\"w\"), indent=2)"; \
	  rm -f /lab/data/events.json.tmp; \
	  echo "Wrote /lab/data/events.json ($$(python3 -c "import json;print(len(json.load(open(\"/lab/data/events.json\"))))") real Windows events)"'

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

demo:
	@echo "=== Module 10 — Detecting Host Compromise ==="
	@echo ""
	@echo "--- Real telemetry: 3 EVTX-ATTACK-SAMPLES phases (persistence / cred-access / lateral) ---"
	docker compose exec lab python3 demo/show_alerts.py data/events.json
	@echo ""
	@echo "--- Running example detection rule (LSASS access, T1003.001) against real events ---"
	docker compose exec lab bash -c '\
		python3 detect.py --rule data/example-rule.yml --events data/events.json'
	@echo ""
	@echo "--- Convert example rule to Splunk SPL ---"
	docker compose exec lab bash -c '\
		sigma convert -t splunk --without-pipeline data/example-rule.yml 2>/dev/null || \
		echo "(sigma-cli: use '\''sigma convert -t splunk --without-pipeline <rule.yml>'\'' to convert rules)"'
	@echo ""
	@echo "=== Run 'make shell' to write your own detection rules ==="
	@echo "    Hint: write rules/persistence-runkey.yml, rules/credaccess-lsass.yml, rules/lateral-service.yml"

shell:
	docker compose exec lab bash
