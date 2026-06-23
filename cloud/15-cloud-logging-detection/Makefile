# Module 15 — Cloud Logging & Detection
# Standard targets: up / down / reset / demo / shell
# Plus the eval harness (Type 13): eval / eval-bad — score the Sigma rule against a HELD-OUT
# CloudTrail corpus and gate on it. Everything runs OFFLINE; there is NO grade target
# (Plaintext is an honor system — no receipts, no grading machinery).
.PHONY: up down reset demo shell detect eval eval-bad

# The detection gate: the rule must catch EVERY held-out attack (recall floor) and fire on NO
# benign near-miss (false-positive ceiling). A rule edit that breaks either fails the build.
RECALL_MIN  ?= 1.0
FP_RATE_MAX ?= 0.0

up:       ## Build and start the lab container
	docker compose up -d --build

down:     ## Stop and remove the container
	docker compose down

reset:    ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:    ## Open a shell in the lab container
	docker compose exec lab bash

# --- The lesson: the eval gate must PASS on the good rule and FAIL on each regression ----------
demo:     ## Run the detector, then prove the eval gate is GREEN on the good rule and RED on regressions.
	docker compose run --rm lab sh -c '\
		set +e; \
		echo "########################################################################"; \
		echo "# A. The bundled detector over the demo events (unchanged)"; \
		echo "########################################################################"; \
		python detect.py data/cloudtrail/events.json; \
		echo; \
		echo "########################################################################"; \
		echo "# B. EVAL: the GOOD Sigma rule on the HELD-OUT corpus — gate should PASS"; \
		echo "########################################################################"; \
		python3 eval_corpus/eval.py --rule data/sigma_rule.yml --gate recall=$(RECALL_MIN) --gate fp_rate=$(FP_RATE_MAX); \
		good=$$?; \
		echo; \
		echo "########################################################################"; \
		echo "# C. EVAL: a REGRESSED rule that DROPS the admin-policy filter (over-broad)"; \
		echo "#         -> fires on legitimate provisioning. Gate should FAIL on fp_rate."; \
		echo "########################################################################"; \
		python3 eval_corpus/eval.py --rule eval_corpus/sigma_rule_regressed.yml --gate recall=$(RECALL_MIN) --gate fp_rate=$(FP_RATE_MAX); \
		broad=$$?; \
		echo; \
		echo "########################################################################"; \
		echo "# D. EVAL: a REGRESSED rule NARROWED to AdministratorAccess only (too tight)"; \
		echo "#         -> goes silent on IAMFullAccess/PowerUserAccess. Gate FAILS on recall."; \
		echo "########################################################################"; \
		python3 eval_corpus/eval.py --rule eval_corpus/sigma_rule_narrow.yml --gate recall=$(RECALL_MIN) --gate fp_rate=$(FP_RATE_MAX); \
		narrow=$$?; \
		echo; \
		echo "=== Verdict ==="; \
		if [ $$good -eq 0 ] && [ $$broad -ne 0 ] && [ $$narrow -ne 0 ]; then \
			echo "PASS: gate is GREEN on the good rule and RED on both regressions — the gate works."; \
			exit 0; \
		else \
			echo "UNEXPECTED: good=$$good (want 0), over-broad=$$broad (want non-zero), narrow=$$narrow (want non-zero)."; \
			exit 1; \
		fi'

eval:     ## Score the GOOD Sigma rule against the held-out corpus and run the gate (exit non-zero on regression).
	docker compose run --rm lab python3 eval_corpus/eval.py --rule data/sigma_rule.yml --gate recall=$(RECALL_MIN) --gate fp_rate=$(FP_RATE_MAX)

eval-bad: ## Score the REGRESSED rules to watch the gate go RED (no exit-on-fail; for inspection).
	docker compose run --rm lab sh -c '\
		echo "--- over-broad (drops admin-policy filter) ---"; \
		python3 eval_corpus/eval.py --rule eval_corpus/sigma_rule_regressed.yml --gate recall=$(RECALL_MIN) --gate fp_rate=$(FP_RATE_MAX) || true; \
		echo; \
		echo "--- too-narrow (AdministratorAccess only) ---"; \
		python3 eval_corpus/eval.py --rule eval_corpus/sigma_rule_narrow.yml --gate recall=$(RECALL_MIN) --gate fp_rate=$(FP_RATE_MAX) || true'

detect:   ## make detect FILE=path/to/events.json — run detector on a custom file
	docker compose run --rm lab python detect.py $(FILE)
