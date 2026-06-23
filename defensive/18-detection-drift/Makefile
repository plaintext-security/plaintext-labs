# Module 18 — Detection Drift lab.
# Standard targets every reference lab provides: up / down / reset / shell / demo.
.PHONY: up down reset shell demo baseline drift-check

up:        ## Build and start the lab container
	docker compose up -d --build

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the lab container
	docker compose exec lab bash

# --- Worked example (the "what good looks like" demo) ---------------------
demo:      ## Drift check at t=0 (healthy) then t=30 (drifted), end to end
	docker compose run --rm lab sh -c '\
		echo "== t=0  BASELINE (healthy estate — should be CLEAN) =="; \
		python drift_check.py \
			--baseline baseline/sources.yml \
			--events data/events_t0.jsonl \
			--corpus corpus/corpus_t0.jsonl \
			--rule rules/encoded_powershell.yml \
			--baseline-recall 1.0; \
		echo; \
		echo "== t=30  OBSERVED (one month later — should detect 3 drifts) =="; \
		echo "   (exits non-zero on purpose: dead source + degraded source + rotted rule)"; \
		python drift_check.py \
			--baseline baseline/sources.yml \
			--events data/events_t30.jsonl \
			--corpus corpus/corpus_t30.jsonl \
			--rule rules/encoded_powershell.yml \
			--baseline-recall 1.0 || true'

# --- Your turn ------------------------------------------------------------
baseline:  ## Snapshot t=0 recall: run the check against the healthy fixtures
	docker compose run --rm lab python drift_check.py \
		--baseline baseline/sources.yml \
		--events data/events_t0.jsonl \
		--corpus corpus/corpus_t0.jsonl \
		--rule rules/encoded_powershell.yml \
		--baseline-recall 1.0

drift-check: ## The scheduled control: run the loop, non-zero exit if drift present
	docker compose run --rm lab python drift_check.py \
		--baseline baseline/sources.yml \
		--events data/events_t30.jsonl \
		--corpus corpus/corpus_t30.jsonl \
		--rule rules/encoded_powershell.yml \
		--baseline-recall 1.0
