.PHONY: up down reset demo shell

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

demo:      ## Run gitleaks detect against data/ and show checklist
	docker compose run --rm lab sh -c '\
		cd /lab && \
		echo "=== gitleaks detect against data/ ==="; \
		git init -q /tmp/demo-repo && \
		cp -r data/ /tmp/demo-repo/ && \
		cd /tmp/demo-repo && \
		git add -A && git -c user.email=lab@example.com git -c user.name=Lab commit -qm "demo" && \
		gitleaks detect --source . --no-banner || true; \
		echo; \
		echo "=== CI Review Checklist ==="; \
		cat /lab/data/ci-review-checklist.md'
