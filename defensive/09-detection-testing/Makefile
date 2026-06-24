# Module 09 — Detection Testing lab.
# No grade target: Plaintext is an honor system. `make eval` is a REGRESSION GATE, not a grader.
.PHONY: up down reset shell demo eval gate fetch-events eval-real

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

# ---------------------------------------------------------------------------
# fetch-events / eval-real — OPT-IN: score the SHIPPED rules over REAL attacker
# telemetry. Clones sbousseaden/EVTX-ATTACK-SAMPLES (real Sysmon EVTX for these
# techniques) via lib/fetch.sh and converts the matching captures into the same
# corpus shape eval.py reads, written to heldout/corpus-real.jsonl (gitignored).
# The committed synthetic heldout/corpus.jsonl stays the deterministic CI gate;
# this is the "point --corpus at real events" move eval.py's header describes.
#
# Runs on the HOST (needs git + python-evtx), not in CI. The real EVTX paths are
# discovered from the clone, so they survive upstream renames within a tree; if a
# file moved, see PROVENANCE.md and adjust the globs below.
# ---------------------------------------------------------------------------
fetch-events: ## Build heldout/corpus-real.jsonl from real EVTX-ATTACK-SAMPLES captures
	pip install --quiet python-evtx
	@. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh" && \
	repo=$$(fetch_repo evtx-attack-samples) && \
	runkey=$$(find "$$repo/Persistence" -iname '*run_key*sysmon_13*.evtx' | head -1) && \
	lsass1=$$(find "$$repo/Credential Access" -iname '*memdump_comsvcs_minidump*.evtx' | head -1) && \
	lsass2=$$(find "$$repo/Credential Access" -iname 'sysmon_10_11_lsass_memdump*.evtx' | head -1) && \
	python3 evtx_to_corpus.py heldout/corpus-real.jsonl \
		"T1547.001:$$runkey" \
		"T1003.001:$$lsass1" \
		"T1003.001:$$lsass2"
	@echo "Done. Score the SHIPPED rules on REAL events with:  make eval-real"

eval-real: ## Scorecard for the shipped rules over the real EVTX corpus (no gate — recall WILL be low; that is the finding)
	docker compose run --rm lab python3 eval.py --corpus heldout/corpus-real.jsonl
