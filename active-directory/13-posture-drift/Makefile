# Module 13 — AD Posture Drift & Steady-State lab.
# Pins a baseline, builds a detect->diff detector, simulates a month of decay, and proves the
# detector names every regression. TWO collection modes: the deterministic seed-file mode (the
# default; reproducible in CI) and a LIVE mode (`make detect-live` / `make baseline-live`) that
# reads posture straight off the bundled Samba DC via ldap3. No `grade` target — honor system.
.PHONY: up down reset shell demo detect drift drift-live reset-state schedule-example detect-live baseline-live

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

reset-state:  ## Restore the clean (no-drift) observed posture
	docker compose exec lab cp data/observed.clean.json data/observed.json
	@echo "observed.json reset to the clean hardened state."

detect:     ## Run the detector: diff observed vs baseline, report per-fact delta (exit 1 on drift)
	docker compose exec lab python3 drift-detect.py

drift:      ## Simulate a month of decay (new SPN, re-added ACE, unexpected DA, stale krbtgt)
	docker compose exec lab bash bin/drift-introduce.sh

drift-live: ## Introduce REAL drift on the DC via samba-tool (new SPN + unexpected Domain Admin)
	docker compose run --rm lab bash bin/drift-introduce.sh --live

demo:       ## t=0 clean (no drift) -> introduce drift -> detector names every regression
	@echo "########################################################################"
	@echo "# t=0 — CLEAN domain. Detector diffs observed vs the declared baseline and"
	@echo "# must report NO DRIFT (empty delta == no false positives)."
	@echo "########################################################################"
	docker compose exec lab sh -c 'cp data/observed.clean.json data/observed.json && python3 drift-detect.py'; \
	  test $$? -eq 0 && echo "[ok] clean domain -> exit 0 (no drift)" || (echo "UNEXPECTED: clean domain reported drift" && exit 1)
	@echo ""
	@echo "########################################################################"
	@echo "# DRIFT — simulate a month of decay, then re-run the detector. It must name"
	@echo "# EACH introduced regression as a concrete fact and exit non-zero."
	@echo "########################################################################"
	docker compose exec lab bash bin/drift-introduce.sh
	@docker compose exec lab sh -c 'python3 drift-detect.py; test $$? -ne 0 && echo "[ok] drift present -> exit non-zero (gate would alert)" || (echo "UNEXPECTED: detector missed the drift" && exit 1)'
	@echo ""
	@echo "=== Verdict ==="
	@echo "PASS: detector is silent on the clean domain and names every regression under drift."
	@echo "Next (do it yourself): adjudicate each delta (bless -> edit baseline.json + commit"
	@echo "who/why; or re-enforce -> remediate, re-run 'make detect', prove empty delta), then"
	@echo "schedule it nightly with cron. See 'make schedule-example' and the lab.md."
	@$(MAKE) --no-print-directory reset-state

baseline-live:  ## Snapshot the LIVE DC posture as data/baseline.live.json (your real starting point)
	docker compose run --rm lab sh -c '\
	    until python3 -c "import socket; socket.create_connection((\"10.10.0.10\", 389), 3)" 2>/dev/null; do sleep 3; done; \
	    python3 drift-detect.py --dump-live > data/baseline.live.json && \
	    echo "[+] wrote data/baseline.live.json from the live DC — review it, then use as your --baseline"'

detect-live:  ## Diff the LIVE DC posture against the baseline (exit 1 on drift) — real ldap3 collection
	docker compose run --rm lab sh -c '\
	    until python3 -c "import socket; socket.create_connection((\"10.10.0.10\", 389), 3)" 2>/dev/null; do sleep 3; done; \
	    python3 drift-detect.py --live --baseline $${BASELINE:-baseline.json}'

schedule-example:  ## Print an example crontab(5) line to run the detector nightly
	@echo "# Run the drift detector every night at 02:00, append the delta to a dated report,"
	@echo "# and let its non-zero exit flag drift for a wrapping alert/gate:"
	@echo "0 2 * * *  cd /lab && python3 drift-detect.py --out \"reports/drift-\$$(date +\\%F).md\" >> /var/log/drift.log 2>&1"
