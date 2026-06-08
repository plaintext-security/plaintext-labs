.PHONY: up down reset shell demo

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose run --rm lab bash

# Run SHA-256, AES, RSA, certificate read, and bit-flip exercises
demo:
	docker compose run --rm lab python3 demo.py
