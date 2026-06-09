# Module 06 — Infrastructure-as-Code Security
# Standard targets: up / down / reset / demo / shell
.PHONY: up down reset demo shell checkov tfsec trivy-config

up:           ## Build the lab container
	docker compose up -d --build

down:         ## Stop and remove the container
	docker compose down

reset:        ## Full teardown — container, image, volumes
	docker compose down --rmi local --volumes --remove-orphans

shell:        ## Open a shell in the lab container
	docker compose exec lab bash

checkov:      ## Run checkov against data/terraform/
	docker compose run --rm lab checkov -d data/terraform --output cli

tfsec:        ## Run tfsec against data/terraform/
	docker compose run --rm lab tfsec data/terraform

trivy-config: ## Run trivy config against data/terraform/
	docker compose run --rm lab trivy config data/terraform

demo:         ## Run all three scanners and summarise findings
	@echo "== 1. checkov =="
	docker compose run --rm lab sh -c '\
		checkov -d data/terraform --output cli --compact 2>/dev/null; \
		echo ""'
	@echo "== 2. tfsec =="
	docker compose run --rm lab sh -c '\
		tfsec data/terraform --format default 2>/dev/null; \
		echo ""'
	@echo "== 3. trivy config =="
	docker compose run --rm lab sh -c '\
		trivy config data/terraform 2>/dev/null; \
		echo ""'
	@echo "== Done. Compare tool coverage in the three outputs above. =="
