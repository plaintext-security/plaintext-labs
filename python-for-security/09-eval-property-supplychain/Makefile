.PHONY: up down reset shell demo test

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

# Reference demo: score the classifier on a HELD-OUT corpus (precision/recall) with a
# regression gate, then run the hypothesis property tests + the supply-chain hash gate.
demo:
	docker compose run --rm lab sh -c "python demo.py && pytest -q"

test:
	docker compose run --rm lab pytest -q
