# Module 17 — Data Protection & KMS lab.
# Standard targets: up / down / reset / demo / shell.
.PHONY: up down reset demo shell envelope check-keypolicy check-fixed

up:        ## Build, seed (create the KMS key), and start (LocalStack + lab container)
	docker compose up -d --build
	@echo "Waiting for seed to complete..."
	@docker compose wait seed || true
	@echo "Lab ready. Run: make demo  or  make shell"

down:      ## Stop and remove containers
	docker compose down

reset:     ## Tear down completely (containers + local images + volumes)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Drop into the lab container (awslocal + openssl available)
	docker compose exec lab bash

envelope:  ## Walk envelope encryption: generate data key -> encrypt -> wrap -> decrypt
	docker compose run --rm lab bash data/envelope.sh

check-keypolicy: ## Check the ORIGINAL (loose) key policy — expect separation to FAIL
	docker compose run --rm lab python3 check_keypolicy.py data/key-policy.json

check-fixed:     ## Check YOUR key-policy-fixed.json — aim for all PASS
	docker compose run --rm lab python3 check_keypolicy.py data/key-policy-fixed.json

demo:      ## Full walkthrough: envelope encryption, then the key-policy separation build->verify
	@echo "== Part 1: envelope encryption (KMS wraps the data key; it never sees your data) =="
	docker compose run --rm lab bash data/envelope.sh
	@echo ""
	@echo "== Part 2: key-policy separation BEFORE the fix (admin missing + app over-granted = FAIL) =="
	-docker compose run --rm lab python3 check_keypolicy.py data/key-policy.json
	@echo ""
	@echo "== Part 2b: separation AFTER the fix (reference policy — all PASS) =="
	docker compose run --rm lab python3 check_keypolicy.py data/key-policy-fixed.json
