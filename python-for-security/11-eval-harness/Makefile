# Module 11 — Eval Harness lab.
# Standard targets every reference lab provides: up / down / reset / shell / demo.
.PHONY: up down reset shell demo classify eval gate test coverage

CORPUS  := data/auth-corpus.jsonl
LABELS  := data/auth-labels.json
RECALL_MIN ?= 0.85

up:        ## Build and start the lab container (python 3.12 + pytest + coverage)
	docker compose up -d --build

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image + volumes)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the lab container
	docker compose exec lab bash

# --- The worked example: gate GREEN on good, RED on the planted regression -----
demo:      ## Score the GOOD parser (gate passes), then the REGRESSED one (gate fails)
	docker compose run --rm lab sh -c '\
		set -e; \
		echo "================ 1. GOOD parser — gate should PASS ================"; \
		if python eval.py --tool scripts/parser_good.py --corpus $(CORPUS) \
			--labels $(LABELS) --gate recall=$(RECALL_MIN); then \
			GOOD_OK=1; else GOOD_OK=0; fi; \
		echo; \
		echo "============ 2. REGRESSED parser — gate should go RED ============"; \
		if python eval.py --tool scripts/parser_regressed.py --corpus $(CORPUS) \
			--labels $(LABELS) --gate recall=$(RECALL_MIN); then \
			REG_OK=1; else REG_OK=0; fi; \
		echo; \
		echo "======================== verdict ========================"; \
		if [ "$$GOOD_OK" = "1" ] && [ "$$REG_OK" = "0" ]; then \
			echo "PASS: gate is GREEN on the good parser and RED on the regression"; \
			exit 0; \
		else \
			echo "UNEXPECTED: good=$$GOOD_OK (want 1)  regressed=$$REG_OK (want 0)"; \
			exit 1; \
		fi'

# --- Your turn: the targets the lab.md walks you through ----------------------
classify:  ## Run the good parser over the corpus -> results/verdicts-good.json
	docker compose run --rm lab sh -c '\
		mkdir -p results && \
		python scripts/parser_good.py $(CORPUS) > results/verdicts-good.json && \
		echo "wrote results/verdicts-good.json"'

eval:      ## Print the full scorecard for the good parser (no gate)
	docker compose run --rm lab python eval.py --tool scripts/parser_good.py \
		--corpus $(CORPUS) --labels $(LABELS)

gate:      ## make gate RECALL_MIN=0.95 — re-run the gate at a stricter recall floor
	docker compose run --rm lab python eval.py --tool scripts/parser_good.py \
		--corpus $(CORPUS) --labels $(LABELS) --gate recall=$(RECALL_MIN)

test:      ## Run the pytest suite (scorer math + parser robustness)
	docker compose run --rm lab python -m pytest tests/ -v

coverage:  ## Coverage of the good parser over the corpus (the coverage-as-foil step)
	docker compose run --rm lab sh -c '\
		coverage run scripts/parser_good.py $(CORPUS) >/dev/null && \
		coverage report -m scripts/parser_good.py'
