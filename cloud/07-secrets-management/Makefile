# Module 07 — Secrets Management & Detection
# Standard targets: up / down / reset / demo / shell
.PHONY: up down reset demo shell scan-history vault-demo dynamic-creds app-run rotate-root aws-secrets

up:           ## Build containers, seed the repo, and configure Vault's dynamic DB engine
	docker compose up -d --build
	docker compose run --rm lab bash data/init-repo.sh
	docker compose run --rm lab bash data/setup-vault-db.sh

down:         ## Stop and remove containers
	docker compose down

reset:        ## Full teardown
	docker compose down --rmi local --volumes --remove-orphans

shell:        ## Open a shell in the lab container
	docker compose exec lab bash

scan-history: ## Run trufflehog against the planted-secret git repo
	docker compose run --rm lab trufflehog git file:///lab/data/repo --no-verification --json

vault-demo:   ## Store and read a static secret in Vault KV (the baseline)
	docker compose run --rm lab sh -c '\
		vault kv put secret/meridian/app/database \
			username=appuser password=db-password-placeholder; \
		vault kv get secret/meridian/app/database'

dynamic-creds: ## Mint a dynamic, 5-minute Postgres credential from Vault
	docker compose run --rm lab sh -c '\
		echo "== Minting a fresh dynamic DB credential (note the TTL) =="; \
		vault read database/creds/app-role'

app-run:      ## Run the app that fetches a dynamic cred at runtime (holds no static secret)
	docker compose run --rm lab python3 data/app_runtime.py

rotate-root:  ## Rotate the Postgres admin password Vault holds (one-way; operator can't read it after)
	docker compose run --rm lab sh -c '\
		echo "== Rotating the root DB password Vault manages =="; \
		vault write -f database/rotate-root/meridian-postgres; \
		echo "Rotated. The admin password is now known only to Vault."'

aws-secrets:  ## The cloud-native variant: Secrets Manager + least-privilege IAM (LocalStack)
	docker compose run --rm lab bash data/setup-aws-secrets.sh

demo:         ## Full worked example: detect → static store → dynamic creds → runtime app → AWS variant
	@echo "== Part 1: trufflehog scans git history =="
	docker compose run --rm lab sh -c '\
		echo "Current HEAD (no creds visible):"; \
		git -C /lab/data/repo log --oneline; \
		echo ""; \
		echo "Running trufflehog (full history scan):"; \
		trufflehog git file:///lab/data/repo --no-verification 2>&1 | head -30; \
		echo ""'
	@echo ""
	@echo "== Part 2: Vault KV — static secret with a least-privilege policy =="
	docker compose run --rm lab sh -c '\
		vault kv put secret/meridian/app/database username=appuser password=db-password-placeholder >/dev/null; \
		vault kv get secret/meridian/app/database'
	@echo ""
	@echo "== Part 3: DYNAMIC credentials — Vault mints a unique, 5-minute DB login on demand =="
	docker compose run --rm lab sh -c 'vault read database/creds/app-role'
	@echo ""
	@echo "== Part 3b: the app fetches that credential AT RUNTIME (no static secret anywhere) =="
	docker compose run --rm lab python3 data/app_runtime.py
	@echo ""
	@echo "== Part 4: cloud-native variant — AWS Secrets Manager + least-privilege IAM policy =="
	docker compose run --rm lab bash data/setup-aws-secrets.sh
