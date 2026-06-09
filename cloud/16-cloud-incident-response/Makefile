# Module 16 — Cloud Incident Response
# Standard targets: up / down / reset / demo / shell
.PHONY: up down reset demo shell triage

up:       ## Build and start the lab container
	docker compose up -d --build

down:     ## Stop and remove the container
	docker compose down

reset:    ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:    ## Open a shell in the lab container
	docker compose exec lab bash

demo:     ## Run triage.py against the bundled incident data and print the timeline
	docker compose run --rm lab python triage.py data/cloudtrail/incident.json data/vpc/flowlogs.csv

triage:   ## make triage CT=path/to/cloudtrail.json FLOW=path/to/flowlogs.csv
	docker compose run --rm lab python triage.py $(CT) $(FLOW)
