.PHONY: up down reset shell demo check

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

demo:
	docker compose run --rm lab python3 audit.py

check:     ## Run the checks in check.yaml to verify your fix (self-check; nothing is recorded)
	python3 ../../scripts/check.py check.yaml
