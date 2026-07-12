.PHONY: up down reset shell demo

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

# Reference demo: valid alerts parse into typed models; malformed alerts are
# REJECTED at the boundary (not silently .get()-ed); secrets load via settings.
demo:
	docker compose run --rm lab python demo.py
