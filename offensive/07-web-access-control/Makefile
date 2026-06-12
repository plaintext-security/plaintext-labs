.PHONY: up down reset shell demo grade

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

demo:
	docker compose run --rm lab python3 audit.py

grade:     ## Grade your fix against grade.yaml (writes receipt.json on pass)
	python3 ../../scripts/grade.py grade.yaml
