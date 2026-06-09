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
	@echo "== Running prowler posture scan against LocalStack =="
	docker compose run --rm lab sh -c '\
		prowler aws \
			--endpoint-url http://localstack:4566 \
			--output-formats json \
			--output-filename /tmp/prowler-demo \
			--severity high critical \
			--no-banner 2>/dev/null || true; \
		echo ""; \
		echo "== Findings (FAIL, HIGH+CRITICAL) =="; \
		jq -r \
			'"'"'["CHECK", "RESOURCE", "SEVERITY", "STATUS"] | @tsv,
			 (.[] | select(.status=="FAIL") | select(.severity | test("high|critical","i"))
			  | [.check_id, (.resource_arn // .resource_id // "n/a"), .severity, .status] | @tsv)'"'"' \
			/tmp/prowler-demo.json 2>/dev/null \
		|| echo "(prowler JSON path may vary by version — see /tmp/prowler-demo* for raw output)"; \
		echo ""; \
		echo "== Summary =="; \
		echo "Total FAIL findings:"; \
		jq '"'"'[.[] | select(.status=="FAIL")] | length'"'"' /tmp/prowler-demo.json 2>/dev/null || echo "see raw output"'
