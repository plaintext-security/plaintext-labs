# Module 04 — Windows Artifacts lab.
# Standard targets: up / down / reset / demo / shell / fetch-data
.PHONY: up down reset demo shell fetch-data

# Real Windows .evtx from the public EVTX-ATTACK-SAMPLES corpus (by sbousseaden),
# pulled from the shared dataset cache (lib/fetch.sh, source name evtx-attack-samples).
# Paths index into the cached clone, so they use real spaces (quoted at copy time).
# See PROVENANCE.md for dataset details and SHA-256 placeholders.
EVTX_FILES := \
	"Lateral Movement/LM_4624_mimikatz_sekurlsa_pth_source_machine.evtx" \
	"Execution/revshell_cmd_svchost_sysmon_1.evtx" \
	"Defense Evasion/DE_1102_security_log_cleared.evtx"

up:  ## Build and start the chainsaw + python-registry container
	docker compose up -d --build

fetch-data:  ## Download the real EVTX-ATTACK-SAMPLES .evtx files into data/ (idempotent)
	@mkdir -p data
	@. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh"; \
	repo=$$(fetch_repo evtx-attack-samples); \
	for f in $(EVTX_FILES); do \
		out="data/$$(basename "$$f")"; \
		if [ -f "$$out" ]; then \
			echo "exists: $$out"; \
		else \
			echo "fetch:  $$out"; \
			cp "$$repo/$$f" "$$out"; \
		fi; \
	done
	@echo "Done. Verify SHA-256 against PROVENANCE.md, then run 'make demo'."

down:  ## Stop and remove the container
	docker compose down

reset:  ## Tear down completely
	docker compose down --rmi local --volumes --remove-orphans

shell:  ## Open a shell in the lab container
	docker compose exec lab bash

demo:  ## Parse bundled EVTX events and registry hive; print key forensic findings
	docker compose run --rm lab python3 parse_artifacts.py
