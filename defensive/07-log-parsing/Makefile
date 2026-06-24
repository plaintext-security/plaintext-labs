# Module 07 — Log Parsing & Normalisation lab.
.PHONY: up down reset shell demo fetch-data

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

# Fetch real public logs to normalise at volume and across TWO formats (sshd + Apache).
# See data/PROVENANCE.md. Not run in CI — you run it locally.
fetch-data: ## Download real loghub OpenSSH + Apache logs → data/raw/
	@mkdir -p data/raw
	. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh" && \
	fetch_file loghub-openssh data/raw/OpenSSH_2k.log && \
	fetch_file loghub-apache data/raw/Apache_2k.log
	@echo "Done. Real logs in data/raw/ — normalise both formats and measure your parse rate:"
	@echo "  python normalize.py data/raw/OpenSSH_2k.log   # sshd lines parse; others fall through"

