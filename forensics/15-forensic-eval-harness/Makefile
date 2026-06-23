# Forensics Module 15 — Forensic Eval Harness.
# Standard targets every reference lab provides: up / down / reset / shell / demo.
.PHONY: up down reset shell demo detect eval

up:        ## Build and start the lab container
	docker compose up -d --build
	@echo "Container ready. Run 'make demo' for the scorecard + regression gate."

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image + volumes)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the lab container
	docker compose exec lab bash

# --- Worked example: the scorecard, then the gate going green then RED ---------
demo:      ## Score the GOOD detectors (gate green), then the REGRESSED ones (gate red)
	docker compose run --rm lab python3 /scripts/eval.py --demo

# --- Your turn -----------------------------------------------------------------
detect:    ## Run the detectors over the corpus → per-file verdicts (data/verdicts.json)
	docker compose run --rm lab python3 /scripts/eval.py --detect

eval:      ## Print the confusion matrix + precision/recall/F1/FP-rate scorecard
	docker compose run --rm lab python3 /scripts/eval.py --score
