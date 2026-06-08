# Module 06 — Web Attacks: Injection lab.
# Standard targets every reference lab provides: up / down / reset / demo.
.PHONY: up down reset demo shell

up:        ## Build and start the vulnerable app (host: http://localhost:8080)
	docker compose up -d --build

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the app container
	docker compose exec webapp bash

demo:      ## Show a benign search, then a UNION injection that steals credentials
	docker compose up -d --build
	docker compose exec -T webapp python /app/demo_attack.py
