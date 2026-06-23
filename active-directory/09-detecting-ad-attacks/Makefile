# Module 09 — Detecting AD Attacks lab.
# No `grade` target: Plaintext is an honor system. `make eval` is a regression gate, not a grader.
.PHONY: up down reset demo shell eval gate

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

demo:       ## Run chainsaw over EVTX samples with bundled Sigma rules
	@echo "=== AD Attack Detection Demo ==="
	@echo ""
	@echo "--- 1. Kerberoasting detection (Event 4769, RC4 etype) ---"
	docker compose run --rm lab sh -c '\
	    chainsaw hunt data/evtx/kerberoast-4769.evtx \
	        -s data/rules/kerberoast.yml \
	        --mapping data/sigma-mappings.yml \
	        --csv 2>/dev/null || \
	    python3 data/evtx_demo.py data/evtx/kerberoast-4769.json kerberoast'
	@echo ""
	@echo "--- 2. DCSync detection (Event 4662, DS-Replication rights) ---"
	docker compose run --rm lab sh -c '\
	    chainsaw hunt data/evtx/dcsync-4662.evtx \
	        -s data/rules/dcsync.yml \
	        --mapping data/sigma-mappings.yml \
	        --csv 2>/dev/null || \
	    python3 data/evtx_demo.py data/evtx/dcsync-4662.json dcsync'
	@echo ""
	@echo "--- 3. AS-REP roasting detection (Event 4768, no preauth) ---"
	docker compose run --rm lab sh -c '\
	    chainsaw hunt data/evtx/asrep-4768.evtx \
	        -s data/rules/asrep.yml \
	        --mapping data/sigma-mappings.yml \
	        --csv 2>/dev/null || \
	    python3 data/evtx_demo.py data/evtx/asrep-4768.json asrep'
	@echo ""
	@echo "--- 4. Pass-the-Hash detection (Event 4624 Type 3 NTLM) ---"
	docker compose run --rm lab sh -c '\
	    chainsaw hunt data/evtx/pth-4624.evtx \
	        -s data/rules/pth.yml \
	        --mapping data/sigma-mappings.yml \
	        --csv 2>/dev/null || \
	    python3 data/evtx_demo.py data/evtx/pth-4624.json pth'
	@echo ""
	@echo "=== Rules summary ==="
	docker compose run --rm lab sh -c \
	    'for r in data/rules/*.yml; do echo "Rule: $$r"; grep "title:" $$r; grep "tags:" $$r -A3 | grep attack; echo; done'
	@echo ""
	@echo "########################################################################"
	@echo "# HELD-OUT EVAL — coverage above is not effectiveness. The detections"
	@echo "# scored against a held-out benign+attack corpus they were NOT tuned on:"
	@echo "# GREEN on the good rules, RED on a rule regressed into noise."
	@echo "########################################################################"
	docker compose run --rm lab sh -c '\
	    set +e; \
	    echo "--- GOOD ruleset on the held-out corpus — gate should PASS ---"; \
	    python3 scripts/eval_detections.py --ruleset good --gate; good=$$?; \
	    echo; \
	    echo "--- REGRESSED ruleset (exclusions dropped) — gate should FAIL ---"; \
	    python3 scripts/eval_detections.py --ruleset regressed --gate; bad=$$?; \
	    echo; \
	    echo "=== Verdict ==="; \
	    if [ $$good -eq 0 ] && [ $$bad -ne 0 ]; then \
	        echo "PASS: gate is GREEN on the good rules and RED on the regression — the gate works."; \
	    else \
	        echo "UNEXPECTED: good=$$good (want 0), regressed=$$bad (want non-zero)."; exit 1; \
	    fi'
	@echo "=== Demo complete. 'make eval' scores the good rules + gate; 'make gate' proves the gate goes RED on the regression; 'make shell' to write your own. ==="

eval:       ## Score the GOOD ruleset on the held-out corpus + enforce the gate (exits non-zero on any miss or false positive)
	docker compose run --rm lab python3 scripts/eval_detections.py --ruleset good --gate

gate:       ## Prove the gate catches a regression: score the deliberately-too-broad ruleset (expects non-zero)
	docker compose run --rm lab python3 scripts/eval_detections.py --ruleset regressed --gate
