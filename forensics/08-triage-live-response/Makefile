.PHONY: up down reset demo shell fetch-data

up:
	docker compose up -d --build
	@echo ""
	@echo "Velociraptor server: http://localhost:8889"
	@echo "Waiting for server to be ready..."
	@sleep 8
	@echo "Environment ready. Run 'make demo' to see artifact collection output."

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

demo:
	@echo "Running simulated VQL artifact collection against BEACHHEAD-WS01..."
	@docker run --rm \
		-v "$(CURDIR)/data:/data" \
		-v "$(CURDIR)/scripts:/scripts" \
		python:3.11-slim \
		sh /scripts/demo.sh

# fetch-data — clone REAL Windows event-log samples (idempotent).
# EVTX-ATTACK-SAMPLES ships genuine ATT&CK-mapped EVTX files; we shallow-clone
# the repo so the learner can compare a real artifact's shape (Execution/,
# Persistence/, LateralMovement/) against the synthetic pslist demo.
# See PROVENANCE.md for the source and terms.
EVTX_REPO ?= https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES
fetch-data:
	@if [ -d data/real/EVTX-ATTACK-SAMPLES ]; then \
		echo "data/real/EVTX-ATTACK-SAMPLES already present — skipping."; \
	else \
		echo "Cloning real EVTX samples from EVTX-ATTACK-SAMPLES..."; \
		mkdir -p data/real && \
		git clone --depth 1 "$(EVTX_REPO)" data/real/EVTX-ATTACK-SAMPLES && \
		echo "Cloned. Pick a Persistence/ or Execution/ EVTX; record its SHA-256 in PROVENANCE.md."; \
	fi

shell:
	docker compose exec lab bash
