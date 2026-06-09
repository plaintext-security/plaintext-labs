# Module 07 — Secrets Management & Detection
# Standard targets: up / down / reset / demo / shell
.PHONY: up down reset demo shell scan-history vault-demo

up:           ## Build containers, start Vault in dev mode, and initialise the seed repo
	docker compose up -d --build
	docker compose run --rm lab bash data/init-repo.sh

down:         ## Stop and remove containers
	docker compose down

reset:        ## Full teardown
	docker compose down --rmi local --volumes --remove-orphans

shell:        ## Open a shell in the lab container
	docker compose exec lab bash

scan-history: ## Run trufflehog against the planted-secret git repo
	docker compose run --rm lab trufflehog git file:///lab/data/repo --no-verification --json

vault-demo:   ## Store and read a secret in Vault dev mode
	docker compose run --rm lab sh -c '\
		echo "== Vault status =="; \
		vault status; \
		echo ""; \
		echo "== Storing secret =="; \
		vault kv put secret/meridian/app/database \
			username=appuser password=db-password-placeholder; \
		echo ""; \
		echo "== Reading secret =="; \
		vault kv get secret/meridian/app/database'

demo:         ## Run the full worked example: secrets scan then Vault store/read
	@echo "== Part 1: trufflehog scans git history =="
	docker compose run --rm lab sh -c '\
		echo "Current HEAD (no creds visible):"; \
		git -C /lab/data/repo log --oneline; \
		echo ""; \
		echo "Running trufflehog (full history scan):"; \
		trufflehog git file:///lab/data/repo --no-verification 2>&1 | head -40; \
		echo ""'
	@echo ""
	@echo "== Part 2: Vault secrets management =="
	docker compose run --rm lab sh -c '\
		vault kv put secret/meridian/app/database \
			username=appuser password=db-password-placeholder; \
		echo ""; \
		vault kv get secret/meridian/app/database; \
		echo ""; \
		echo "Secret stored and retrieved. Rotate:"; \
		vault kv put secret/meridian/app/database \
			username=appuser password=db-password-rotated; \
		vault kv get secret/meridian/app/database; \
		echo ""; \
		echo "Version history:"; \
		vault kv metadata get secret/meridian/app/database'
