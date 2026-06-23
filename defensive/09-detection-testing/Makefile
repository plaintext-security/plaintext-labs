# Module 09 — Detection Testing lab.
# No grade target: Plaintext is an honor system. `make eval` is a REGRESSION GATE, not a grader.
.PHONY: up down reset shell demo eval gate

# The malicious-class recall floor for the held-out corpus. A change that drops recall below
# this is a regression and fails the build.
RECALL_MIN ?= 0.90

up:
	docker compose up -d --build
down:
	docker compose down
reset:
	docker compose down --rmi local --volumes --remove-orphans
shell:
	docker compose exec lab bash

# demo = the purple-team loop (unchanged) THEN the eval harness: gate GREEN on the good
# rules, RED on the planted regression. The contrast IS the lesson.
demo:
	docker compose run --rm lab sh -c '\
		python3 test_detections.py; \
		echo; \
		echo "########################################################################"; \
		echo "# EVAL HARNESS — score the rules on the HELD-OUT corpus + regression gate"; \
		echo "########################################################################"; \
		set +e; \
		echo "--- 1. GOOD rules on the held-out set — gate should PASS ---"; \
		python3 eval.py --gate recall=$(RECALL_MIN); good=$$?; \
		echo "--- 2. REGRESSED rules (narrowed encoded-PS match) — gate should FAIL ---"; \
		python3 eval.py --rules heldout/rules-regressed --gate recall=$(RECALL_MIN); bad=$$?; \
		echo; echo "=== Verdict ==="; \
		if [ $$good -eq 0 ] && [ $$bad -ne 0 ]; then \
			echo "PASS: gate is GREEN on the good rules and RED on the regression — it cannot silently regress."; \
			exit 0; \
		else \
			echo "UNEXPECTED: good=$$good (want 0), regressed=$$bad (want non-zero)."; exit 1; \
		fi'

# eval = score the good rules on the held-out corpus and enforce the recall gate (exits non-zero on regression).
eval:
	docker compose run --rm lab python3 eval.py --gate recall=$(RECALL_MIN)

# gate = prove the regression is caught: run the eval against the deliberately-regressed ruleset (expects non-zero).
gate:
	docker compose run --rm lab python3 eval.py --rules heldout/rules-regressed --gate recall=$(RECALL_MIN)
