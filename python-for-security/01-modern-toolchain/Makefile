.PHONY: up down reset shell demo

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

# Reference demo: the legacy script runs, the migrated `sift` reproduces its output
# byte-for-byte, and the ruff gate is clean — the migration broke nothing.
demo:
	docker compose run --rm lab python demo.py
