# Module 12 — Tiering a Brownfield Domain lab (deterministic SIMULATION).
# Models the flat AD state + PATH-001 as a graph; tiers it in waves and proves, per wave,
# that no admin is locked out AND the targeted attack hop is dead. No live Samba DC — the
# GPO Deny-logon user-rights that close the path are enforced client-side by the Windows
# LSA, which these labs don't ship; see VALIDATION.md. No `grade` target — honor system.
.PHONY: up down reset shell demo before check

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

before:     ## Re-walk PATH-001 on the FLAT domain — prove it reaches Domain Admin (t=0)
	docker compose run --rm lab python3 flat-walk.py

check:      ## Run the cumulative per-wave two-part gate (no-lockout AND attack-dead)
	docker compose run --rm lab python3 wave-check.py --cumulative

demo:       ## Full story: PATH-001 open on the flat domain, then dead after tiering in waves
	@echo "########################################################################"
	@echo "# BEFORE — the flat brownfield domain. A Domain Admin logs on to a Tier 2"
	@echo "# workstation, so PATH-001 runs to Domain Admin. This is the t=0 reality."
	@echo "########################################################################"
	docker compose run --rm lab python3 flat-walk.py
	@echo ""
	@echo "########################################################################"
	@echo "# MIGRATE — tier the domain in waves (pilot OU -> Protected Users -> widen)."
	@echo "# Each wave must keep legitimate admins logged on AND kill its target hop."
	@echo "########################################################################"
	docker compose run --rm lab python3 wave-check.py --cumulative
	@echo ""
	@echo "=== AFTER ==="
	@echo "PATH-001's credential-harvest hop is dead while tallen still administers from"
	@echo "the Tier 0 jump host (JUMP01) and sgarcia still works on the Tier 2 boxes."
	@echo "Run 'make shell' then 'python3 wave-check.py --wave wave-1 --json' to inspect"
	@echo "a single wave, or write your own migration-runbook.md and wave plan."
