# Module 04 — Cloud Network Security lab.
# Standard targets: up / down / reset / demo / shell.
.PHONY: up down reset demo shell audit flows

up:        ## Build and start the lab container
	docker compose up -d --build
	@echo "Lab ready. Run: make demo  or  make shell"

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Drop into the lab container (cloudmapper + Python available)
	docker compose exec lab bash

# --- Worked example: Security Group audit + flow log analysis ---------------
demo:      ## Run the full network security analysis walkthrough
	docker compose run --rm lab python demo.py

# --- Individual targets for interactive work ---------------------------------
audit:     ## Run cloudmapper audit against bundled account JSON
	docker compose run --rm lab cloudmapper audit --account meridian --config data/config.json

flows:     ## Run VPC flow log anomaly analysis
	docker compose run --rm lab python analyze_flows.py data/vpc-flow-logs.log
