.PHONY: up down reset shell demo

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

# Reference demo: the shell=True wrapper EXECUTES an injected command; the
# shell=False + validated wrapper refuses the same payload. Injection, then fix.
demo:
	docker compose run --rm lab python demo.py
