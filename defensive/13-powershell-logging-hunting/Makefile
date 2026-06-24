# Defensive Module 13 — PowerShell Logging & Hunting lab.
# Standard targets every reference lab provides: up / down / reset / demo [/ shell].
.PHONY: up down reset shell demo hunt fetch-data

up:        ## Build and start the lab container
	docker compose up -d --build

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a PowerShell prompt in the lab container
	docker compose exec lab pwsh

demo:      ## Worked hunt: flag the malicious script blocks in the bundled 4104 log
	docker compose run --rm lab pwsh -NoProfile -File /lab/hunt.ps1

hunt:      ## make hunt FILE=mylog.json — run the hunt against your own 4104 export
	docker compose run --rm lab pwsh -NoProfile -File /lab/hunt.ps1 -Path $(FILE)

# Fetch a real 4104 EVTX and rebuild data/scriptblock-4104.json from it (see data/PROVENANCE.md).
# NOT run in CI — you run it locally. Requires git + python-evtx (pip install python-evtx).
EVTX_SAMPLE ?= Other/emotet/exec_emotet_ps_4104.evtx
fetch-data: ## Clone EVTX-ATTACK-SAMPLES and convert a real 4104 capture → data/scriptblock-4104.json
	pip install --quiet python-evtx
	. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh" && \
	repo=$$(fetch_repo evtx-attack-samples) && \
	python3 convert_evtx.py "$$repo/$(EVTX_SAMPLE)" data/scriptblock-4104.json
	@echo "Done. data/scriptblock-4104.json now holds REAL 4104 records — hunt with: make demo"
