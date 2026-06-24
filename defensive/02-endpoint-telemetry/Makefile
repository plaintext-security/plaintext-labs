# Module 02 — Endpoint Telemetry lab.
.PHONY: up down reset shell demo fetch-data
up:
	docker compose up -d --build
down:
	docker compose down
reset:
	docker compose down --rmi local --volumes --remove-orphans
shell:
	docker compose exec lab bash
demo:
	docker compose run --rm lab python3 analyze.py
fetch-data: ## Pull a real Sysmon EVTX from EVTX-ATTACK-SAMPLES and convert it to JSON analyze.py reads
	@command -v git >/dev/null || { echo "git required"; exit 1; }
	pip install python-evtx >/dev/null
	. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh" && \
	repo=$$(fetch_repo evtx-attack-samples) && \
	python3 evtx_to_json.py \
	  "$$repo/Execution/exec_sysmon_1_lolbin_rundll32_advpack_RegisterOCX.evtx" \
	  > data/real_sysmon_events.json
	@echo "Wrote data/real_sysmon_events.json — analyze it with: python3 analyze.py data/real_sysmon_events.json"
	@echo "See data/PROVENANCE.md for source, sample path, and license."
