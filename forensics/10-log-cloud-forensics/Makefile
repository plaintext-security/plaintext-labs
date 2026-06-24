.PHONY: up down reset demo shell fetch-data

# Real Windows .evtx from the public EVTX-ATTACK-SAMPLES corpus (by sbousseaden),
# pulled from the shared dataset cache (lib/fetch.sh, source name evtx-attack-samples).
# Paths index into the cached clone, so they use real spaces (quoted at copy time).
# See PROVENANCE.md for dataset details and SHA-256 placeholders.
EVTX_FILES := \
	"Lateral Movement/LM_4624_mimikatz_sekurlsa_pth_source_machine.evtx" \
	"Execution/revshell_cmd_svchost_sysmon_1.evtx"

up:
	docker compose up -d --build
	@echo "Container ready. Run 'make fetch-data' then 'make demo'."

fetch-data:  ## Download the real EVTX-ATTACK-SAMPLES .evtx files into data/evtx/ (idempotent)
	@mkdir -p data/evtx
	@. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh"; \
	repo=$$(fetch_repo evtx-attack-samples); \
	for f in $(EVTX_FILES); do \
		out="data/evtx/$$(basename "$$f")"; \
		if [ -f "$$out" ]; then \
			echo "exists: $$out"; \
		else \
			echo "fetch:  $$out"; \
			cp "$$repo/$$f" "$$out"; \
		fi; \
	done
	@echo "Done. Verify SHA-256 against PROVENANCE.md, then run 'make demo'."

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

demo:
	docker compose exec lab sh /scripts/demo.sh

shell:
	docker compose exec lab bash
