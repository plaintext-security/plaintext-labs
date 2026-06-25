# Module 12 — Tiering a Brownfield Domain lab.
# Models the flat AD state + PATH-001 as a graph; tiers it in waves and proves, per wave, that
# no admin is locked out AND the targeted attack hop is dead. The GPO Deny-logon user-rights are
# enforced client-side by the Windows LSA (which these labs don't ship), so that ENFORCEMENT
# stays modelled — but the directory FACTS the model rests on are verified live against the
# bundled Samba DC by `make corroborate` (ldap3). See VALIDATION.md. No `grade` — honor system.
.PHONY: up down reset shell demo before check corroborate

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

corroborate: ## Verify the flat baseline fixture against the LIVE DC (rosters, SPN surface) via ldap3
	docker compose run --rm lab sh -c '\
	    until python3 -c "import socket; socket.create_connection((\"10.10.0.10\", 389), 3)" 2>/dev/null; do sleep 3; done; \
	    python3 corroborate-live.py'

before:     ## Re-walk PATH-001 on the FLAT domain — prove it reaches Domain Admin (t=0)
	docker compose exec lab python3 flat-walk.py

check:      ## Run the cumulative per-wave two-part gate (no-lockout AND attack-dead)
	docker compose exec lab python3 wave-check.py --cumulative

demo:       ## Full story: PATH-001 open on the flat domain, then dead after tiering in waves
	@echo "########################################################################"
	@echo "# BEFORE — the flat brownfield domain. A Domain Admin logs on to a Tier 2"
	@echo "# workstation, so PATH-001 runs to Domain Admin. This is the t=0 reality."
	@echo "########################################################################"
	docker compose exec lab python3 flat-walk.py
	@echo ""
	@echo "########################################################################"
	@echo "# MIGRATE — tier the domain in waves (pilot OU -> Protected Users -> widen)."
	@echo "# Each wave must keep legitimate admins logged on AND kill its target hop."
	@echo "########################################################################"
	docker compose exec lab python3 wave-check.py --cumulative
	@echo ""
	@echo "=== AFTER ==="
	@echo "PATH-001's credential-harvest hop is dead while tallen still administers from"
	@echo "the Tier 0 jump host (JUMP01) and sgarcia still works on the Tier 2 boxes."
	@echo "Run 'make shell' then 'python3 wave-check.py --wave wave-1 --json' to inspect"
	@echo "a single wave, or write your own migration-runbook.md and wave plan."
