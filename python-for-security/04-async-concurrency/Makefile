.PHONY: up down reset shell demo

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

# Reference demo: enrich many indicators against a local mock TI API with BOUNDED
# concurrency (a semaphore) and backoff on HTTP 429 — no thundering herd, no ban.
demo:
	docker compose run --rm lab python demo.py
