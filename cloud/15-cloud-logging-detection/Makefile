# Module 15 — Cloud Logging & Detection
# Standard targets: up / down / reset / demo / shell
.PHONY: up down reset demo shell detect

up:       ## Build and start the lab container
	docker compose up -d --build

down:     ## Stop and remove the container
	docker compose down

reset:    ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:    ## Open a shell in the lab container
	docker compose exec lab bash

demo:     ## Run the bundled detector against the seed CloudTrail events
	docker compose run --rm lab python detect.py data/cloudtrail/events.json

detect:   ## make detect FILE=path/to/events.json — run detector on a custom file
	docker compose run --rm lab python detect.py $(FILE)
