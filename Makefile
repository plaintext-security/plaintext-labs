# Repo-level dev tasks for the shared lab tooling under scripts/.
# (Each lab has its own Makefile with up/down/reset/demo.)
.PHONY: test validate dev-deps

dev-deps:   ## Install the test/lint toolchain (pytest, PyYAML)
	python3 -m pip install -r scripts/requirements-dev.txt

test:       ## Run the scripts pytest suite (offline; no Docker/network)
	python3 -m pytest scripts/tests/ -q

