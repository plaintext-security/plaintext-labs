.PHONY: up down reset shell demo

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

# Shell with your current directory mounted — write topips.py here and it persists
shell:
	docker compose run --rm lab bash

# Show expected output + Python building blocks for topips.py
demo:
	docker compose run --rm lab python3 demo.py
