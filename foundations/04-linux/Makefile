.PHONY: up down reset shell demo

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose run --rm lab bash

# Show expected triage output (users, SUID, processes, log analysis)
demo:
	docker compose run --rm lab python3 demo.py
