# Module 05 — Posture & Misconfiguration Auditing
# Standard targets: up / down / reset / demo / shell
.PHONY: up down reset demo shell

up:        ## Build containers and seed the misconfigured LocalStack environment
	docker compose up -d --build
	@echo "Waiting for LocalStack to be ready..."
	@docker compose exec lab bash -c 'until curl -sf http://localstack:4566/_localstack/health | grep -q "\"s3\": \"running\""; do sleep 2; done'
	docker compose run --rm lab bash data/setup.sh

down:      ## Stop and remove containers
	docker compose down

reset:     ## Full teardown — containers, images, volumes
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the lab container (LocalStack accessible as http://localstack:4566)
	docker compose exec lab bash

demo:      ## Run prowler against the seeded LocalStack account and show HIGH/CRITICAL findings
	docker compose run --rm lab bash data/scan.sh
