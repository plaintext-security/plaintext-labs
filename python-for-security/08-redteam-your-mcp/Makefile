.PHONY: up down reset shell demo test

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

# Reference demo: land an INDIRECT injection through poisoned enrichment data,
# then show the guard neutralize it, then run the regression test that locks it.
demo:
	docker compose run --rm lab sh -c "python demo.py && pytest -q"

test:
	docker compose run --rm lab pytest -q
