# Module 07 — Timeline Analysis lab.
# Standard targets: up / down / reset / demo / shell / l2t / fetch-data
.PHONY: up down reset demo shell l2t fetch-data

# Real Windows .evtx from the public EVTX-ATTACK-SAMPLES corpus (by sbousseaden) — an execution
# chain (cmd/svchost reverse shell, Sysmon EID 1) that plaso parses natively into the timeline.
# See PROVENANCE.md for dataset details, exact URL, and SHA-256 placeholder.
EVTX_URL := https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Execution/revshell_cmd_svchost_sysmon_1.evtx

up:  ## Build and start the plaso container
	docker compose up -d --build

fetch-data:  ## Download a real EVTX-ATTACK-SAMPLES .evtx into data/artifacts/ (idempotent)
	@mkdir -p data/artifacts
	@if [ -f data/artifacts/revshell_cmd_svchost_sysmon_1.evtx ]; then \
		echo "exists: data/artifacts/revshell_cmd_svchost_sysmon_1.evtx"; \
	else \
		echo "fetch:  data/artifacts/revshell_cmd_svchost_sysmon_1.evtx"; \
		curl -fsSL "$(EVTX_URL)" -o data/artifacts/revshell_cmd_svchost_sysmon_1.evtx; \
	fi
	@echo "Done. Verify SHA-256 against PROVENANCE.md, then run 'make l2t' to timeline the real .evtx."

down:  ## Stop and remove the container
	docker compose down

reset:  ## Tear down completely
	docker compose down --rmi local --volumes --remove-orphans

shell:  ## Open a shell in the lab container
	docker compose exec lab bash

demo:  ## Analyze pre-computed timeline (data/timeline.csv) and display incident narrative
	docker compose run --rm lab python3 analyze_timeline.py

# Run log2timeline against the bundled artifact directory
# Produces a plaso storage file, then exports a filtered incident-window CSV
l2t:  ## Run log2timeline + psort on data/artifacts/ (builds from raw artifacts)
	docker compose run --rm lab sh -c '\
		echo "=== Step 1: log2timeline.py — ingest artifacts ==="; \
		log2timeline.py /tmp/timeline.plaso data/artifacts/ 2>&1; \
		echo; \
		echo "=== Step 2: psort.py — export all events ==="; \
		psort.py -o l2tcsv /tmp/timeline.plaso 2>/dev/null | head -30; \
		echo; \
		echo "=== Step 3: psort.py — filter to incident window ==="; \
		psort.py -o l2tcsv \
			--slice "2024-03-15T02:00:00" \
			--slice_size 35 \
			/tmp/timeline.plaso 2>/dev/null | head -50; \
		echo; \
		echo "=== Demo complete. For richer analysis, use: make demo ==="'
