# Module 07 — Log Parsing & Normalisation lab.
.PHONY: up down reset shell demo

up:        ## Build and start the lab container
	docker compose up -d --build

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the lab container
	docker compose exec lab bash

demo:      ## Normalise the sample log and report the parse rate (incl. unparsed lines)
	docker compose run --rm lab python normalize.py data/auth_sample.txt
