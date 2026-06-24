.PHONY: up down reset demo shell fetch

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

fetch:     ## (needs network) pull the full 2,000-line loghub OpenSSH corpus into data/sshd.log
	docker compose run --rm lab python data/fetch_log.py

demo:      ## Run the reference parser and show top offending IPs
	docker compose run --rm lab python parse_log.py
