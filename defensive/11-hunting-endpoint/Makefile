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
	docker compose run --rm lab python3 hunt.py

# Fetch the real Sysmon EVTX and rebuild data/sysmon_events.json from it (see data/PROVENANCE.md).
# NOT run in CI — you run it locally. Requires git + python-evtx (pip install python-evtx).
EVTX_SAMPLE ?= Execution/exec_persist_rundll32_mshta_scheduledtask_sysmon_1_3_11.evtx
fetch-data: ## Clone EVTX-ATTACK-SAMPLES and convert a real Sysmon capture → data/sysmon_events.json
	pip install --quiet python-evtx
	. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh" && \
	repo=$$(fetch_repo evtx-attack-samples) && \
	python3 convert_evtx.py "$$repo/$(EVTX_SAMPLE)" data/sysmon_events.json
	@echo "Done. data/sysmon_events.json now holds the REAL Sysmon events — hunt with: python3 hunt.py"
