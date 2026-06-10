# Module 04 — Hashing, MACs & Passwords
# Standard targets: up / down / reset / demo / shell

.PHONY: up down reset demo shell

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

demo:
	@echo "=== Module 04 — Hashing, MACs & Passwords Demo ==="
	@echo ""
	@echo "--- Part 1: SHA-256 hash cracking simulation ---"
	docker compose exec lab python3 /lab/demo/part1_crack.py
	@echo ""
	@echo "--- Part 2: Argon2id password hashing (correct approach) ---"
	docker compose exec lab python3 /lab/demo/part2_argon2.py
	@echo ""
	@echo "=== Run 'make shell' for the full cracking and HMAC exercises ==="

shell:
	docker compose exec lab bash
