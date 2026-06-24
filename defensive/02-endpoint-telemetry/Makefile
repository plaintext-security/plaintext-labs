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
	git clone --depth 1 https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES.git data/EVTX-ATTACK-SAMPLES
	pip install python-evtx >/dev/null
	python3 evtx_to_json.py \
	  "data/EVTX-ATTACK-SAMPLES/Execution/exec_sysmon_1_lolbin_rundll32_advpack_RegisterOCX.evtx" \
	  > data/real_sysmon_events.json
	@echo "Wrote data/real_sysmon_events.json — analyze it with: python3 analyze.py data/real_sysmon_events.json"
	@echo "See data/PROVENANCE.md for source, sample path, and license."
