# Module 11 — AI Evaluation & Observability lab.
# Standard targets every reference lab provides: up / down / reset / demo.
# Everything here is pure Python stdlib and runs OFFLINE against recorded predictions —
# no live model, no GPU. There is NO grade target: Plaintext is an honor system.
.PHONY: up down reset shell demo eval eval-rag gate classify

# Triage gate: the malicious-class recall floor. A regression below this fails the build.
TRIAGE_RECALL_MIN ?= 0.80
# RAG gate: the retrieval@k floor.
RAG_RECALL_MIN ?= 0.75

up:        ## Start the lab container
	docker compose up -d

down:      ## Stop the container
	docker compose down

reset:     ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the lab container
	docker compose exec lab bash

# --- The lesson: a gate must PASS on the good system and FAIL on the regression ----------
demo:      ## Score the good system (gate passes), then the regression (gate fails). The contrast IS the lesson.
	docker compose run --rm lab sh -c '\
		set +e; \
		echo "########################################################################"; \
		echo "# 1. GOOD triage system on the held-out corpus — the gate should PASS"; \
		echo "########################################################################"; \
		python3 scripts/eval.py triage --predictions data/predictions-good.json --gate recall=$(TRIAGE_RECALL_MIN); \
		good=$$?; \
		echo; \
		echo "########################################################################"; \
		echo "# 2. REGRESSED triage system (under-classifies attacks) — gate should FAIL"; \
		echo "########################################################################"; \
		python3 scripts/eval.py triage --predictions data/predictions-regressed.json --gate recall=$(TRIAGE_RECALL_MIN); \
		bad=$$?; \
		echo; \
		echo "########################################################################"; \
		echo "# 3. RAG retrieval — GOOD (gate passes) then REGRESSED (gate fails)"; \
		echo "########################################################################"; \
		python3 scripts/eval.py rag --retrieval data/retrieval-good.json --gate recall_at_k=$(RAG_RECALL_MIN); \
		python3 scripts/eval.py rag --retrieval data/retrieval-regressed.json --gate recall_at_k=$(RAG_RECALL_MIN); \
		echo; \
		echo "=== Verdict ==="; \
		if [ $$good -eq 0 ] && [ $$bad -ne 0 ]; then \
			echo "PASS: gate is GREEN on the good system and RED on the regression — the gate works."; \
			exit 0; \
		else \
			echo "UNEXPECTED: good=$$good (want 0), regressed=$$bad (want non-zero)."; \
			exit 1; \
		fi'

eval:      ## Score the good triage predictions and print the scorecard (no gate)
	docker compose run --rm lab python3 scripts/eval.py triage --predictions data/predictions-good.json

eval-rag:  ## Score the good RAG retrieval and print retrieval@k
	docker compose run --rm lab python3 scripts/eval.py rag --retrieval data/retrieval-good.json

gate:      ## Run the triage gate on the good predictions (exits non-zero on regression)
	docker compose run --rm lab python3 scripts/eval.py triage --predictions data/predictions-good.json --gate recall=$(TRIAGE_RECALL_MIN)

classify:  ## Run the deterministic STUB classifier to (re)generate predictions, then score them
	docker compose run --rm lab sh -c '\
		python3 scripts/stub_classifier.py --out results/predictions-stub.json; \
		python3 scripts/eval.py triage --predictions results/predictions-stub.json'
