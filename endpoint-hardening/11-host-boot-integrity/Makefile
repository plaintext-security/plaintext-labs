# Module 11 — Host & Boot Integrity lab.
# Standard targets: up / down / reset / demo / shell, plus tamper / check.
.PHONY: up down reset demo shell tamper check check-clean

up:      ## Build the host image, start it, and build the known-good AIDE baseline
	docker compose up -d --build
	@echo "Building the AIDE baseline (known-good snapshot)..."
	docker compose exec -T host bash data/setup.sh
	@echo "Lab ready. Try:  make check  (clean)  |  make tamper  then  make check"

down:    ## Stop and remove the container
	docker compose down

reset:   ## Tear down completely (container + local image + volumes) for a clean rebuild
	docker compose down --rmi local --volumes --remove-orphans

shell:   ## Drop into the host (aide CLI + the watched tree available)
	docker compose exec host bash

tamper:  ## Plant three changes: modified binary, new SUID-root file, dropped cron
	docker compose exec -T host bash data/tamper.sh

check:   ## Run AIDE --check and assert behaviour (auto: clean before tamper, detects after)
	docker compose exec -T host bash check_integrity.sh

check-clean: ## Assert the fresh baseline reports NO changes (run right after `make up`)
	docker compose exec -T host bash check_integrity.sh --baseline-clean

demo:    ## Full walkthrough: clean baseline -> plant tamper -> AIDE detects all three
	@echo "============================================================"
	@echo "  Lab 11 — Host & Boot Integrity (AIDE file-integrity)"
	@echo "============================================================"
	@echo ""
	@echo "== Part 1: a fresh baseline must report CLEAN =="
	-docker compose exec -T host bash check_integrity.sh --baseline-clean
	@echo ""
	@echo "== Part 2: an attacker lands and plants three changes =="
	docker compose exec -T host bash data/tamper.sh
	@echo ""
	@echo "== Part 3: AIDE's known-good comparison catches all three =="
	-docker compose exec -T host bash check_integrity.sh --detects
	@echo ""
	@echo "============================================================"
	@echo "  Integrity = 'has this changed from known-good?' — proven."
	@echo "  (The baseline DB is the trust anchor — protect it off-box.)"
	@echo "============================================================"
