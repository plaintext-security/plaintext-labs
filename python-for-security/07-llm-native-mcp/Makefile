.PHONY: up down reset shell demo

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

# Reference demo: the MCP tool validates every (untrusted) LLM-supplied argument;
# the typed-output discipline (what instructor does) rejects a malformed model reply.
demo:
	docker compose run --rm lab python demo.py
