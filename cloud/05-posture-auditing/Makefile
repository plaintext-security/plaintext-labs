# Module 05 — Posture & Misconfiguration Auditing
# Standard targets: up / down / reset / demo / shell
.PHONY: up down reset demo shell

up:        ## Build containers and seed the misconfigured floci environment
	docker compose up -d --build
	@echo "Waiting for floci to be ready..."
	@docker compose exec lab bash -c 'until curl -sf http://floci:4566/_localstack/health | grep -qE "\"s3\": ?\"running\""; do sleep 2; done'
	docker compose run --rm lab bash data/setup.sh

down:      ## Stop and remove containers
	docker compose down

reset:     ## Full teardown — containers, images, volumes
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the lab container (floci accessible as http://floci:4566)
	docker compose exec lab bash

demo:      ## Run prowler against the seeded floci account and show HIGH/CRITICAL findings
	docker compose run --rm lab bash data/scan.sh
