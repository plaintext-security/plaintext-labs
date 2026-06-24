# Module 08 — Path to Domain Admin lab.
# A live BloodHound collection against the DC, then offline path analysis.
.PHONY: up down reset shell collect demo

up:         ## Start the Samba DC + a bloodhound-python collector container
	docker compose up -d --build

down:       ## Stop and remove containers
	docker compose down

reset:      ## Tear down completely
	docker compose down --rmi local --volumes --remove-orphans

shell:      ## Open a shell in the collector container
	docker compose exec collector bash

collect:    ## Run a REAL BloodHound collection against the live DC (writes data/*.json + zip)
	@echo "=== Collecting from dc01.corp.local as jsmith (live LDAP/SMB) ==="
	docker compose exec collector sh -c \
	    'cd /data && bloodhound-python -u jsmith -p "Welcome1!" -d corp.local \
	        -dc dc01.corp.local -ns 10.10.0.10 -c All --zip 2>&1 | tail -20'
	@echo "=== Collected BloodHound JSON is under data/ — import the .zip into BloodHound CE ==="

demo:       ## Analyse the attack paths with ATT&CK mapping (reference dataset)
	@echo "NOTE: 'make collect' produces the LIVE graph from the DC for import into BloodHound CE."
	@echo "      The analysis below runs over the curated reference path dataset (schema example)."
	@echo ""
	@python3 data/path-analyzer.py data/bloodhound-attack-paths.json
