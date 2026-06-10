# Module 05 — ACL & Delegation Abuse lab.
.PHONY: up down reset demo shell

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec attacker bash

demo:       ## Identify ACL misconfigurations and show the attack path
	@echo "=== Waiting for DC... ==="
	docker compose exec attacker sh -c \
	    'until python3 -c "import socket; socket.create_connection((\"dc01.meridian.local\", 389), 3)" 2>/dev/null; do sleep 3; done; echo "DC ready."'
	@echo ""
	@echo "=== 1. Query unconstrained delegation accounts ==="
	docker compose exec attacker ldapsearch \
	    -H ldap://dc01.meridian.local \
	    -x -D 'jsmith@MERIDIAN.LOCAL' -w 'Welcome1!' \
	    -b 'DC=meridian,DC=local' \
	    '(userAccountControl:1.2.840.113556.1.4.803:=524288)' \
	    sAMAccountName userAccountControl \
	    2>/dev/null | grep "^sAMAccountName:"
	@echo ""
	@echo "=== 2. Meridian ACL Findings Summary ==="
	python3 demo/acl_findings.py data/acl-findings.json
	@echo ""
	@echo "=== 3. Attack path summary ==="
	python3 demo/attack_paths.py data/acl-findings.json
	@echo ""
	@echo "=== Demo complete. Run 'make shell' to explore interactively. ==="
