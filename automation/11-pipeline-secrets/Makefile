# Module 11 — Secrets Handling in Pipelines (OIDC) lab.
# Standard targets: up / down / reset / demo / shell, plus bad / oidc / jwks / check.
.PHONY: up down reset demo shell bad oidc jwks check check-loose

up:      ## Build, start LocalStack, register the IAM OIDC provider + scoped deploy role
	docker compose up -d --build
	@echo "Waiting for seed (IAM OIDC provider + role) to complete..."
	@docker compose wait seed || true
	@echo "Lab ready. Try:  make bad   |   make oidc   |   make demo   |   make shell"

down:    ## Stop and remove containers
	docker compose down

reset:   ## Tear down completely (containers + local image + volumes)
	docker compose down --rmi local --volumes --remove-orphans

shell:   ## Drop into the runner container (awslocal + the mint/check tooling)
	docker compose exec runner bash

bad:     ## Run the BEFORE pipeline: deploy with a STORED long-lived key (the leak surface)
	docker compose exec -T runner bash data/pipeline-bad.sh

oidc:    ## Run the AFTER pipeline: federate via AssumeRoleWithWebIdentity for short-lived creds
	docker compose exec -T runner bash data/pipeline-oidc.sh

jwks:    ## (Optional) serve the OIDC provider's JWKS endpoint, as a real STS would fetch
	docker compose exec runner python3 data/serve_jwks.py

check:   ## Prove it: no stored static key, credential is short-lived + the trust policy is scoped
	docker compose exec -T runner python3 check_no_static_secret.py

check-loose: ## Show the checker CATCHES a wildcard sub (run against the loose trust policy)
	docker compose exec -T runner python3 check_no_static_secret.py --trust data/trust-policy-loose.json

demo:    ## Full walkthrough: the static-key BEFORE, the OIDC AFTER, then the proof
	@echo "============================================================"
	@echo "  Lab 11 — Secrets Handling in Pipelines (OIDC)"
	@echo "============================================================"
	@echo ""
	@echo "== BEFORE: deploy with a stored long-lived key (what gitleaks hunts) =="
	-docker compose exec -T runner bash data/pipeline-bad.sh
	@echo ""
	@echo "== AFTER: federate for a short-lived credential — no stored key =="
	docker compose exec -T runner bash data/pipeline-oidc.sh
	@echo ""
	@echo "== PROOF: no static secret, credential short-lived, trust policy scoped =="
	docker compose exec -T runner python3 check_no_static_secret.py
	@echo ""
	@echo "== Negative check: the SAME checker FAILS on a wildcard-sub trust policy =="
	-docker compose exec -T runner python3 check_no_static_secret.py --trust data/trust-policy-loose.json
	@echo ""
	@echo "============================================================"
	@echo "  No secret to leak. The off-switch is the trust policy."
	@echo "============================================================"
