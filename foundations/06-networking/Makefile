.PHONY: up down reset shell demo

up:
	docker compose up -d server lab

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

# Drop into the lab container with all network tools (tcpdump, dig, curl)
shell:
	docker compose run --rm lab bash

# Live DNS + HTTP demo + annotated capture walk-through
demo:
	docker compose run --rm demo
