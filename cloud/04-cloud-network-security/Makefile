# Module 04 — Cloud Network Security lab.
# Standard targets: up / down / reset / demo / shell.
.PHONY: up down reset demo shell audit flows reachability reachability-fixed

up:        ## Build and start the lab container
	docker compose up -d --build
	@echo "Lab ready. Run: make demo  or  make shell"

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Drop into the lab container (cloudmapper + Python available)
	docker compose exec lab bash

# --- Worked example: audit -> author the fix -> verify reachability ----------
demo:      ## Full walkthrough: SG/flow audit, then the reachability build->verify loop
	docker compose run --rm lab python demo.py
	@echo ""
	@echo "== Reachability BEFORE the fix (the two findings show ALLOW = FAIL) =="
	-docker compose run --rm lab python check_reachability.py data/account/meridian/describe-security-groups.json
	@echo ""
	@echo "== Reachability AFTER the fix (reference remediated groups — all PASS) =="
	docker compose run --rm lab python check_reachability.py data/account/meridian/security-groups-fixed.json

# --- Individual targets for interactive work ---------------------------------
audit:     ## Run cloudmapper audit against bundled account JSON
	docker compose run --rm lab cloudmapper audit --account meridian --config data/config.json

flows:     ## Run VPC flow log anomaly analysis
	docker compose run --rm lab python analyze_flows.py data/vpc-flow-logs.log

reachability:       ## Check reachability against the ORIGINAL (bad) groups — expect FAILs
	docker compose run --rm lab python check_reachability.py data/account/meridian/describe-security-groups.json

reachability-fixed: ## Check reachability against YOUR security-groups-fixed.json — aim for all PASS
	docker compose run --rm lab python check_reachability.py data/account/meridian/security-groups-fixed.json
