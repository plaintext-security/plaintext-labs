# Module 11 — Defending Identity lab.
# Design module with a LIVE compliance check: `make compliance` runs tier-compliance-check.py
# against the bundled Samba DC to prove whether the running domain obeys the tiered-admin design.
.PHONY: demo up down reset shell compliance

up:         ## Start the Samba DC + the compliance-check container
	docker compose up -d --build

down:       ## Stop and remove containers
	docker compose down

reset:      ## Tear down completely
	docker compose down --rmi local --volumes --remove-orphans

shell:      ## Open a shell in the lab container
	docker compose exec lab bash

compliance: ## Run the LIVE tiered-admin compliance check against the DC (ldap3; exit 1 on any fail)
	docker compose run --rm lab sh -c '\
	    until python3 -c "import socket; socket.create_connection((\"10.10.0.10\", 389), 3)" 2>/dev/null; do sleep 3; done; \
	    python3 tier-compliance-check.py'

demo:       ## Print the defense control matrix
	@echo "=== Corp — Defense Control Summary ==="
	@echo ""
	@echo "PREVENTION CONTROLS (eliminate the attack surface)"
	@echo "  T1558.003 Kerberoasting:        Migrate to gMSA (eliminates crackable hash)"
	@echo "  T1558.004 AS-REP Roast:         Remove DONT_REQUIRE_PREAUTH flag"
	@echo "  T1550.002 Pass-the-Hash:        Protected Users + Credential Guard + Tiering"
	@echo "  T1003.006 DCSync:               Restrict DS-Replication rights to DCs only"
	@echo "  T1021.002 SMB Lateral Movement: SMB signing required + LAPS + Tiering"
	@echo "  T1558.001 Golden Ticket:        Auth Policy Silos + krbtgt double rotation"
	@echo "  T1484.001 ACL Abuse:            Audit/remove non-default write ACEs + JIT"
	@echo ""
	@echo "DETECTION CONTROLS (observe the attack)"
	@echo "  T1558.003: Event 4769 with TicketEncryptionType=0x17 (RC4)"
	@echo "  T1558.004: Event 4768 with PreAuthType=0"
	@echo "  T1003.006: Event 4662 with DS-Replication GUID from non-DC account"
	@echo "  T1550.002: Event 4624 LogonType=3 AuthPackage=NTLM unusual source"
	@echo "  T1484.001: Event 4728 (member added to privileged group)"
	@echo ""
	@echo "TIERED ADMIN MODEL — Corp"
	@echo "  Tier 0 (Control Plane): dc01, dc02 | Accounts: tallen, Administrator"
	@echo "  Tier 1 (Management Plane): fs01, backup01, wsus01 | Accounts: sgarcia, pmartinez"
	@echo "  Tier 2 (User Plane): WS-FIN-*, WS-HR-*, WS-IT-* | Accounts: Finance, HR users"
	@echo ""
	@echo "  Rule: Tier 0 credentials NEVER touch Tier 1 or Tier 2 hosts"
	@echo "  Rule: Tier 1 credentials NEVER touch Tier 2 hosts"
	@echo "  Enforcement: GPO Deny logon locally + Deny logon via RDS on lower tiers"
	@echo ""
	@echo "ARCHITECTURAL ANSWER TO PATH-001"
	@echo "  Step 1 (Kerberoast):       gMSA eliminates crackable hash"
	@echo "  Step 2 (Credential reuse): Unique passwords; spray detection"
	@echo "  Step 3 (GenericWrite):     ACL remediation removes the edge"
	@echo "  Step 4 (PTH to DC):        Tiering blocks non-Tier-0 DC logon"
	@echo "  Step 5 (DCSync):           Protected Users + ACL audit + detection"
	@echo ""
	@echo "Full control matrix: cat data/defense-controls.md"
