# Module 12 — Configuration & Posture Drift
# Standard targets: up / down / reset / shell / demo
# Loop targets:     baseline / drift / detect / reconcile / loop
#
# Single privileged container = Ansible controller + hardened target (localhost),
# the Module-06 shape. Everything runs locally in Docker, zero cloud cost.
.PHONY: up down reset shell baseline drift detect reconcile loop demo

up:        ## Build, start, and converge the target to the declared baseline (t=0)
	docker compose up -d --build
	@echo "Converging the target to the declared baseline (t=0, zero drift)..."
	docker compose exec lab bash -lc 'ansible-playbook -i /opt/inventory /lab/data/playbook.yml \
		2>&1 | grep -E "(PLAY RECAP)"'

down:      ## Stop and remove the container
	docker compose down

reset:     ## Revert any drift, then tear down completely
	-docker compose exec lab bash -lc 'bash /lab/data/drift.sh undo' 2>/dev/null || true
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the controller/target
	docker compose exec lab bash

baseline:  ## Converge to the declared baseline and confirm zero drift (--check --diff)
	docker compose exec lab bash -lc 'ansible-playbook -i /opt/inventory /lab/data/playbook.yml \
		2>&1 | grep -E "(PLAY RECAP)"'
	@echo "--- Confirm zero drift at t=0 (--check --diff should report nothing would change) ---"
	docker compose exec lab bash -lc 'bash /lab/data/drift-loop.sh detect'

drift:     ## Inject three realistic drifts (sysctl flip, re-opened root SSH, world-writable file)
	docker compose exec lab bash -lc 'bash /lab/data/drift.sh inject'

detect:    ## Run the detector: control-named delta (what changed, which control) — not a score
	docker compose exec lab bash -lc 'bash /lab/data/drift-loop.sh detect'

reconcile: ## Re-apply the baseline so observed re-converges to declared
	docker compose exec lab bash -lc 'bash /lab/data/drift-loop.sh reconcile'

loop:      ## The full steady-state beat: detect -> diff -> alert -> reconcile
	docker compose exec lab bash -lc 'bash /lab/data/drift-loop.sh loop'

# --- Worked example (the "what good looks like" demo) ---------------------
demo:      ## baseline (zero drift) -> drift -> detect (named delta x3) -> reconcile -> zero drift -> loop (alert)
	@echo "=== Module 12 — Drift: detect -> diff -> reconcile -> alert ==="
	@echo
	@echo "== 1. Baseline: confirm zero drift at t=0 (observed == declared) =="
	-docker compose exec lab bash -lc 'bash /lab/data/drift-loop.sh detect'
	@echo
	@echo "== 2. Inject drift (the world acting on the host) =="
	docker compose exec lab bash -lc 'bash /lab/data/drift.sh inject'
	@echo
	@echo "== 3. Detect: control-named delta for all three drifts (not a score) =="
	-docker compose exec lab bash -lc 'bash /lab/data/drift-loop.sh detect'
	@echo
	@echo "== 4. Loop: alert on the delta FIRST, then reconcile back to baseline =="
	-docker compose exec lab bash -lc 'bash /lab/data/drift-loop.sh loop'
	@echo
	@echo "== 5. Detect again: clean host is SILENT (delta only, no false alarm) =="
	docker compose exec lab bash -lc 'bash /lab/data/drift-loop.sh detect'
	@echo
	@echo "=== Run 'make shell' to explore the baseline, drift.sh, and drift-loop.sh ==="
