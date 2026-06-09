# Module 03 — IAM Attack Paths lab.
# Standard targets: up / down / reset / demo / shell.
.PHONY: up down reset demo shell analyze

up:        ## Build, seed, and start (LocalStack + lab container)
	docker compose up -d --build
	@echo "Waiting for seed to complete..."
	@docker compose wait seed || true
	@echo "Lab ready. Run: make demo  or  make shell"

down:      ## Stop and remove containers
	docker compose down

reset:     ## Tear down completely (containers + images + volumes)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Drop into the lab container
	docker compose exec lab bash

# --- Worked example: find all paths to admin in the bundled graph ----------
demo:      ## Run the attack-path analysis against the bundled graph.json
	@docker compose run --rm lab sh -c '\
		echo "=== 1. IAM principals in the seeded account ==="; \
		awslocal iam list-users --query "Users[*].UserName" --output table; \
		awslocal iam list-roles --query "Roles[*].RoleName" --output table; \
		echo; \
		echo "=== 2. Analyze the bundled graph for paths to admin ==="; \
		python analyze.py data/graph.json; \
		exit 0; \
	' || true
	@echo
	@echo "Exit code non-zero = paths to admin found (expected for this scenario)."

# --- Run analyze against a custom graph ------------------------------------
analyze:   ## make analyze GRAPH=data/graph.json — run path finder against any graph file
	docker compose run --rm lab python analyze.py $(GRAPH)
