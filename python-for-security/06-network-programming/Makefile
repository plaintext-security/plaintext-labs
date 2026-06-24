.PHONY: up down reset demo shell

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

demo:      ## Run reference scanner + banner grabber against the target container
	docker compose run --rm lab python scanner.py --host target --ports 8983,5005,9999
