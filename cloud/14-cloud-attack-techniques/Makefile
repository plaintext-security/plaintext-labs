# Module 14 — Cloud Attack Techniques
# Standard targets: up / down / reset / demo / shell
.PHONY: up down reset demo shell

up:       ## Build and start LocalStack + lab container
	docker compose up -d --build

down:     ## Stop and remove containers
	docker compose down

reset:    ## Tear down completely (containers, volumes, images)
	docker compose down --rmi local --volumes --remove-orphans

shell:    ## Open a shell in the lab container
	docker compose exec lab bash

demo:     ## Run the full attack simulation and print CloudTrail-shaped output
	docker compose exec lab bash -c './simulate.sh'
