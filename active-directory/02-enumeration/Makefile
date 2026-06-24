# Module 02 — Enumeration lab.
# Standard targets: up / down / reset / demo / shell
.PHONY: up down reset demo shell

up:         ## Build and start the Samba DC + attacker containers
	docker compose up -d --build

down:       ## Stop and remove containers
	docker compose down

reset:      ## Tear down completely (containers + volumes + images)
	docker compose down --rmi local --volumes --remove-orphans

shell:      ## Open a shell in the attacker container
	docker compose exec attacker bash

demo:       ## Run automated ldapsearch enumeration against the Corp DC
	@echo "=== Waiting for DC to be ready... ==="
	docker compose exec attacker sh -c 'until ldapsearch -H ldap://dc01.corp.local -x -D "jsmith@CORP.LOCAL" -w "Welcome1!" -b "DC=corp,DC=local" "(objectClass=domain)" dc 2>/dev/null | grep -q "dc: corp"; do sleep 3; done; echo "DC ready."'
	@echo ""
	@echo "=== 1. All user accounts ==="
	docker compose exec attacker ldapsearch \
	    -H ldap://dc01.corp.local \
	    -x -D "jsmith@CORP.LOCAL" -w "Welcome1!" \
	    -b "DC=corp,DC=local" \
	    "(objectClass=user)" \
	    sAMAccountName userPrincipalName \
	    2>/dev/null | grep -E "^sAMAccountName:|^dn:" | head -40
	@echo ""
	@echo "=== 2. Kerberoastable accounts (have SPN) ==="
	docker compose exec attacker ldapsearch \
	    -H ldap://dc01.corp.local \
	    -x -D "jsmith@CORP.LOCAL" -w "Welcome1!" \
	    -b "DC=corp,DC=local" \
	    "(&(objectClass=user)(servicePrincipalName=*))" \
	    sAMAccountName servicePrincipalName \
	    2>/dev/null | grep -E "^sAMAccountName:|^servicePrincipalName:"
	@echo ""
	@echo "=== 3. AS-REP roastable accounts (no pre-auth) ==="
	docker compose exec attacker ldapsearch \
	    -H ldap://dc01.corp.local \
	    -x -D "jsmith@CORP.LOCAL" -w "Welcome1!" \
	    -b "DC=corp,DC=local" \
	    "(&(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=4194304))" \
	    sAMAccountName \
	    2>/dev/null | grep "^sAMAccountName:"
	@echo ""
	@echo "=== 4. Groups and memberships ==="
	docker compose exec attacker ldapsearch \
	    -H ldap://dc01.corp.local \
	    -x -D "jsmith@CORP.LOCAL" -w "Welcome1!" \
	    -b "DC=corp,DC=local" \
	    "(objectClass=group)" \
	    cn member \
	    2>/dev/null | grep -E "^cn:|^member:" | head -30
	@echo ""
	@echo "=== Demo complete. Run 'make shell' to explore interactively. ==="
