.PHONY: up down reset demo shell fetch-data

# Real Windows .evtx from the public EVTX-ATTACK-SAMPLES corpus (by sbousseaden).
# See PROVENANCE.md for dataset details, exact URLs, and SHA-256 placeholders.
EVTX_BASE := https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master
EVTX_FILES := \
	Lateral%20Movement/LM_4624_mimikatz_sekurlsa_pth_source_machine.evtx \
	Execution/revshell_cmd_svchost_sysmon_1.evtx

up:
	docker compose up -d --build
	@echo "Container ready. Run 'make fetch-data' then 'make demo'."

fetch-data:  ## Download the real EVTX-ATTACK-SAMPLES .evtx files into data/evtx/ (idempotent)
	@mkdir -p data/evtx
	@for f in $(EVTX_FILES); do \
		out="data/evtx/$$(basename $$f)"; \
		if [ -f "$$out" ]; then \
			echo "exists: $$out"; \
		else \
			echo "fetch:  $$out"; \
			curl -fsSL "$(EVTX_BASE)/$$f" -o "$$out"; \
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
