.PHONY: up down reset shell demo

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

# Reference demo: the SAME core (pydantic models + triage) is driven by a typer
# CLI and a FastAPI endpoint; both return byte-identical results. One core, two surfaces.
demo:
	docker compose run --rm lab python demo.py
