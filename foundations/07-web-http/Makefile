.PHONY: up down reset shell demo

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

# Shell with curl available. Two targets to read:
#   http://echo-server:8080  — the legible teaching echo server
#   http://juice-shop:3000   — the REAL OWASP intentionally-vulnerable app
#                              (point your header-audit script here)
shell:
	docker compose run --rm lab bash

# Run the HTTP mechanics demo (GET, POST, redirect, cookie, role header)
demo:
	docker compose run --rm lab python3 demo.py
