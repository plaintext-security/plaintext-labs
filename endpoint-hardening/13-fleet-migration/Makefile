# Module 13 — Fleet Migration
# Standard targets: up / down / reset / shell / demo
# Rollout targets:  health / roll RING=... / rollback RING=...
#
# A single Ansible-controller container models an in-service fleet of ~6 hosts
# (each serving an HTTP /health endpoint). The baseline rolls ring by ring
# (test -> canary -> fleet) with a service-health gate. Zero cloud cost.
.PHONY: up down reset shell health roll rollback demo

SERIAL ?= 2
MAXFAIL ?= 25
EXC ?= 0

up:        ## Build, start, and bring up the in-service fleet (all serving, unhardened)
	docker compose up -d --build
	docker compose exec lab bash -lc '/lab/data/fleet.sh init'

down:      ## Stop and remove the container
	docker compose down

reset:     ## Stop the fleet apps, then tear down completely
	-docker compose exec lab bash -lc '/lab/data/fleet.sh stop' 2>/dev/null || true
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the controller
	docker compose exec lab bash

health:    ## Service-health across ALL hosts (serving + hardened-for-profile). make health [EXPECT=yes]
	docker compose exec lab bash -lc '/lab/fleet-health.sh all $(if $(EXPECT),$(EXPECT),no)'

roll:      ## Roll a ring: make roll RING=test|canary|fleet [SERIAL=2 MAXFAIL=25 EXC=1]
	docker compose exec lab bash -lc '/lab/data/rollout.sh roll $(RING) $(SERIAL) $(MAXFAIL) $(EXC)'

rollback:  ## Per-ring rollback: make rollback RING=canary
	docker compose exec lab bash -lc '/lab/data/rollout.sh back $(RING)'

# --- Worked example (the "what good looks like" demo) ---------------------
demo:      ## health -> roll test -> roll canary (legacy breaks) -> exception -> rollback+re-roll -> roll fleet -> final health
	@echo "=== Module 13 — staged fleet rollout, ring by ring, no outage ==="
	@echo
	@echo "== 1. Starting state: every host in service (200) BEFORE any hardening =="
	docker compose exec lab bash -lc '/lab/fleet-health.sh all no'
	@echo
	@echo "== 2. Roll the TEST ring (hardened AND still serving) =="
	docker compose exec lab bash -lc '/lab/data/rollout.sh roll test 1 25 0'
	@echo
	@echo "== 3. Roll the CANARY (incl. legacy) under FULL baseline — legacy app BREAKS =="
	-docker compose exec lab bash -lc '/lab/data/rollout.sh roll canary 2 25 0'
	@echo "   (expected: the canary after-check FAILS — host-05 compliant but DOWN.)"
	@echo
	@echo "== 4. Apply the DEFENDED EXCEPTION (relaxed profile for the legacy host), re-roll canary =="
	docker compose exec lab bash -lc '/lab/data/rollout.sh roll canary 2 25 1'
	@echo
	@echo "== 5. Per-ring ROLLBACK of the canary, then re-roll (a rollback you actually run) =="
	docker compose exec lab bash -lc '/lab/data/rollout.sh back canary'
	docker compose exec lab bash -lc '/lab/data/rollout.sh roll canary 2 25 1'
	@echo
	@echo "== 6. Roll the FLEET in batches (serial=2, max_fail=25%, health-gated per batch) =="
	docker compose exec lab bash -lc '/lab/data/rollout.sh roll fleet 2 25 0'
	@echo
	@echo "== 7. Final fleet-wide proof: every host hardened (or exception) AND still serving =="
	docker compose exec lab bash -lc '/lab/fleet-health.sh all yes'
	@echo
	@echo "=== Run 'make shell' to explore rollout.sh, fleet-health.sh, and the rolling playbook ==="
