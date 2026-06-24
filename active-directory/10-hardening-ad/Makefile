# Module 10 — Hardening AD as Code lab.
.PHONY: up down reset demo shell

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec hardening-tools bash

demo:       ## Run ACL audit against the Corp DC + print hardening checklist summary
	@echo "=== Waiting for DC... ==="
	docker compose exec hardening-tools sh -c \
	    'until python3 -c "import socket; socket.create_connection((\"dc01.corp.local\", 389), 3)" 2>/dev/null; do sleep 3; done; echo "DC ready."'
	@echo ""
	@echo "=== 1. ACL audit — IT-Admins group (who has write rights?) ==="
	docker compose exec hardening-tools \
	    dacledit.py CORP.LOCAL/tallen:'T@ll3n_IT@dmin!'@dc01.corp.local \
	    -action read -target-dn 'CN=IT-Admins,CN=Users,DC=corp,DC=local' 2>/dev/null | \
	    grep -E "GenericWrite|WriteDacl|WriteOwner|AllExtendedRights" || \
	    echo "[note] Run dacledit.py manually for full ACL output"
	@echo ""
	@echo "=== 2. Kerberoastable accounts ==="
	docker compose exec hardening-tools ldapsearch \
	    -H ldap://dc01.corp.local \
	    -x -D 'tallen@CORP.LOCAL' -w 'T@ll3n_IT@dmin!' \
	    -b 'DC=corp,DC=local' \
	    '(&(objectClass=user)(servicePrincipalName=*))' \
	    sAMAccountName servicePrincipalName \
	    2>/dev/null | grep -E "^sAMAccountName:|^servicePrincipalName:"
	@echo ""
	@echo "=== 3. AS-REP roastable accounts ==="
	docker compose exec hardening-tools ldapsearch \
	    -H ldap://dc01.corp.local \
	    -x -D 'tallen@CORP.LOCAL' -w 'T@ll3n_IT@dmin!' \
	    -b 'DC=corp,DC=local' \
	    '(&(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=4194304))' \
	    sAMAccountName \
	    2>/dev/null | grep "^sAMAccountName:" || echo "(none found — good!)"
	@echo ""
	@echo "=== 4. Unconstrained delegation ==="
	docker compose exec hardening-tools ldapsearch \
	    -H ldap://dc01.corp.local \
	    -x -D 'tallen@CORP.LOCAL' -w 'T@ll3n_IT@dmin!' \
	    -b 'DC=corp,DC=local' \
	    '(userAccountControl:1.2.840.113556.1.4.803:=524288)' \
	    sAMAccountName \
	    2>/dev/null | grep "^sAMAccountName:"
	@echo ""
	@echo "=== 5. Hardening checklist summary ==="
	@echo "   See data/hardening-checklist.md for full CIS-aligned gap analysis"
	@echo "   See data/ad-hardening.yml for the Ansible remediation playbook"
	@echo ""
	@echo "=== Demo complete. Run 'make shell' to explore interactively. ==="
