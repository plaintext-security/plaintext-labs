.PHONY: up down reset shell demo

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose run --rm lab bash

# Decode real artifacts: base64 PS command, hex C2 domain, URL path traversal, KEV feed
demo:
	docker compose run --rm lab python3 demo.py
