.PHONY: up down reset shell demo

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

# Shell with curl available (use curl against http://echo-server:8080)
shell:
	docker compose run --rm lab bash

# Run the HTTP mechanics demo (GET, POST, redirect, cookie, role header)
demo:
	docker compose run --rm lab python3 demo.py
