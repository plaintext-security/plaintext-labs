.PHONY: up down reset demo shell test test-local smoke

# Default model/source can be overridden: `make demo CURRICULUM_DIR=/path/to/plaintext/tracks`

up:        ## Build the image and start the server container (idle; clients exec/launch it)
	docker compose up -d --build

down:      ## Stop the container
	docker compose down

reset:     ## Tear down completely (image + volumes + orphans)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the running container
	docker compose exec mcp bash

demo:      ## Prove the server loads the curriculum and serves the MCP protocol over stdio
	@echo "=== Plaintext Curriculum MCP — Demo ==="
	@echo ""
	@echo "Step 1: server self-check (loads the bundled curriculum snapshot)"
	docker compose run --rm mcp python3 server/server.py --selfcheck
	@echo ""
	@echo "Step 2: offline smoke test (parser + query layer)"
	docker compose run --rm mcp python3 tests/smoke_test.py
	@echo ""
	@echo "Step 3: MCP stdio round-trip (a client lists tools, calls one, reads a resource)"
	docker compose run --rm mcp python3 tests/mcp_roundtrip.py

test:      ## Run smoke + round-trip tests inside the container
	docker compose run --rm mcp python3 tests/smoke_test.py
	docker compose run --rm mcp python3 tests/mcp_roundtrip.py

# --- run without Docker (a local venv) ---------------------------------------

smoke:     ## Run the dependency-free smoke test with the host python3 (no install)
	python3 tests/smoke_test.py

test-local: ## Create a venv, install deps, run both tests on the host
	python3 -m venv .venv
	.venv/bin/pip install -q -r server/requirements.txt
	.venv/bin/python tests/smoke_test.py
	.venv/bin/python tests/mcp_roundtrip.py
