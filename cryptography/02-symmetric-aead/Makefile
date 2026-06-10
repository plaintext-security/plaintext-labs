# Module 02 — Symmetric & AEAD
# Standard targets: up / down / reset / demo / shell

.PHONY: up down reset demo shell

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

demo:
	@echo "=== Module 02 — Symmetric Encryption & AEAD Demo ==="
	@echo ""
	@echo "--- Part 1: GCM IV reuse attack ---"
	docker compose exec lab python3 /lab/demo/part1_iv_reuse.py
	@echo ""
	@echo "--- Part 2: Correct implementation (random IV per encryption) ---"
	docker compose exec lab python3 /lab/demo/part2_random_iv.py
	@echo ""
	@echo "=== Run 'make shell' for the full IV reuse and AAD exercises ==="

shell:
	docker compose exec lab bash
