.PHONY: up down reset shell demo target-up target-down

# The scan target is the Vulhub nginx CVE-2017-7529 environment — a real,
# named CVE (integer overflow in the nginx range filter, nginx <= 1.13.2,
# leaks cache file headers/memory). It is pulled on demand from the shared
# dataset cache (`fetch_repo vulhub`) and stood up on host :8080. The
# scanner enumerates it and version detection reveals an nginx in the
# vulnerable range — the real CVE that feeds module 03. Vulhub is not
# committed here.

up:        ## Build the scanner and stand up the Vulhub nginx CVE-2017-7529 target
	docker compose up -d --build
	@$(MAKE) target-up

down:      ## Stop the scanner and the Vulhub target
	@$(MAKE) target-down
	docker compose down

reset:     ## Tear down completely (containers + local image + target)
	@$(MAKE) target-down
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the scanner container
	docker compose exec lab bash

demo:      ## Run the three-phase nmap scan against the Vulhub target (:8080 via host)
	docker compose run --rm lab python3 scan.py host.docker.internal 8080

# --- The scan target (Vulhub nginx CVE-2017-7529) — pulled on demand -----------
# Clones Vulhub once into the shared cache, then starts its nginx
# CVE-2017-7529 compose (publishes on host :8080). Requires Docker Hub access.
target-up: ## Clone + start the Vulhub nginx CVE-2017-7529 target (:8080)
	. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh" && \
	repo=$$(fetch_repo vulhub) && \
	cd "$$repo/nginx/CVE-2017-7529" && docker compose up -d
	@echo "Waiting for the Vulhub nginx target to listen on :8080..."
	@# The scanner races the target otherwise: scan.py exits non-zero when it
	@# finds no open ports. Poll :8080 with curl (any HTTP response, including
	@# 4xx, means nginx is up) until it answers, or fail fast with a clear
	@# message rather than handing demo a dead target.
	@i=0; until curl -s -o /dev/null --max-time 2 http://localhost:8080/; do \
		i=$$((i+1)); \
		if [ $$i -gt 60 ]; then echo "Target did not come up on :8080 in time."; exit 1; fi; \
		printf '.'; sleep 2; \
	done
	@echo ""
	@echo "Target up: http://localhost:8080/  (nginx CVE-2017-7529 — scan it)"

target-down: ## Stop the Vulhub target
	@. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh" && \
	repo=$$(fetch_repo vulhub) && \
	cd "$$repo/nginx/CVE-2017-7529" && docker compose down || true
