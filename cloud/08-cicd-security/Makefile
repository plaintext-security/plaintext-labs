# Module 08 — CI/CD Pipeline Security
# Standard targets: up / down / reset / demo / shell
.PHONY: up down reset demo shell gitleaks trivy-scan

up:         ## Build the lab container and initialise the seed repository
	docker compose up -d --build
	docker compose run --rm lab bash data/init-repo.sh

down:       ## Stop and remove the container
	docker compose down

reset:      ## Full teardown
	docker compose down --rmi local --volumes --remove-orphans

shell:      ## Open a shell in the lab container
	docker compose exec lab bash

gitleaks:   ## Run gitleaks against the seeded repository
	docker compose run --rm lab gitleaks detect \
		--source /lab/data/repo \
		--report-format json \
		--report-path /tmp/gitleaks-report.json \
		--no-banner; \
	docker compose run --rm lab jq '.[].RuleID' /tmp/gitleaks-report.json

trivy-scan: ## Scan the first image in data/images.txt (requires network)
	docker compose run --rm lab sh -c '\
		IMAGE=$$(head -1 /lab/data/images.txt | grep -v "^#" | tr -d " "); \
		echo "Scanning: $$IMAGE"; \
		trivy image --severity HIGH,CRITICAL "$$IMAGE"'

demo:       ## Run both scanners and display summary findings
	@echo "== 1. gitleaks: scanning data/repo for secrets =="
	-docker compose run --rm lab sh -c '\
		gitleaks detect \
			--source /lab/data/repo \
			--report-format json \
			--report-path /tmp/gl.json \
			--no-banner 2>/dev/null; \
		echo "Findings:"; \
		jq -r '"'"'.[].RuleID'"'"' /tmp/gl.json 2>/dev/null || echo "(see /tmp/gl.json)"'
	@echo ""
	@echo "== 2. trivy: scanning python:3.8-slim for known CVEs (requires network) =="
	docker compose run --rm lab sh -c '\
		trivy image --severity HIGH,CRITICAL --no-progress python:3.8-slim 2>/dev/null | tail -20 \
		|| echo "Network not available — trivy image scan requires internet access"'
	@echo ""
	@echo "== 3. Review data/workflow.yml — identify the 7 misconfigurations =="
	docker compose run --rm lab sh -c '\
		echo "Issues annotated in data/workflow.yml:"; \
		grep "# ISSUE" /lab/data/workflow.yml'
