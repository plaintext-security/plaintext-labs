.PHONY: up down reset shell demo

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

# Reference demo — the before/after: the trusting starter (sift_starter/)
# accepts garbage or crashes on the messy feed; the typed boundary
# (sift_reference/) rejects every malformed record; secrets load via settings.
demo:
	docker compose run --rm lab python demo.py
