# Module 12 — Choosing Your Crypto lab.
# Standard targets: up / down / reset / shell / demo, plus `lint` for your own ADRs.
.PHONY: up down reset shell demo lint

up:        ## Build and start the lab container
	docker compose up -d --build

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the lab container
	docker compose exec lab bash

# --- Worked example (the "what good looks like" demo) ---------------------
# Run the linter over BOTH samples: the good ADR passes; the broken one fails
# the gate (no standard cited, empty Consequences, missing "What would change
# this"). The good file alone must exit 0; the pair together exits non-zero,
# proving the gate fires. We show both, deterministically.
demo:      ## Lint the sample ADRs: good one passes, broken one fails the gate
	@echo "== 1. The GOOD ADR passes the gate (exit 0) =="
	docker compose run --rm lab python adr-lint.py data/sample-adr-good.md
	@echo
	@echo "== 2. The BROKEN ADR fails the gate (exit 1 — expected) =="
	-docker compose run --rm lab python adr-lint.py data/sample-adr-bad.md
	@echo
	@echo "Gate fires on bad input and passes good input — that is the point."

# --- Your turn: point the linter at the ADRs you write --------------------
lint:      ## make lint DIR=adr — lint every .md in your ADR directory
	docker compose run --rm lab sh -c 'python adr-lint.py $(or $(DIR),adr)/*.md'
