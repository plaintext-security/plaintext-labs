# Module 08 — Secret Detection & Leakage
# Standard targets: up / down / reset / demo / shell

.PHONY: up down reset demo shell

up:
	docker compose up -d --build
	@# The ./:/lab bind mount shadows the image-built repo, so (re)build it at runtime.
	docker compose exec lab bash /lab/data/init-repo.sh

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

demo:
	@echo "=== Module 08 — Secret Detection & Leakage Demo ==="
	@echo ""
	@echo "--- Repository commit history ---"
	docker compose exec lab bash -c '\
		git -C /lab/data/repo log --oneline'
	@echo ""
	@echo "--- Current state (latest commit) — no visible credentials ---"
	docker compose exec lab bash -c '\
		cat /lab/data/repo/src/config.py'
	@echo ""
	@echo "--- gitleaks scans FULL history — finds the deleted credentials ---"
	docker compose exec lab bash -c '\
		gitleaks detect --source /lab/data/repo --verbose 2>/dev/null | \
		grep -E "(Finding|Secret|Commit|File|RuleID)" | head -30 || \
		echo "gitleaks scan complete"'
	@echo ""
	@echo "--- trufflehog cross-validates findings ---"
	docker compose exec lab bash -c '\
		trufflehog git file:///lab/data/repo --no-verification 2>/dev/null | \
		head -30 || echo "trufflehog scan complete"'
	@echo ""
	@echo "Key lesson: deleting a file does NOT remove it from git history."
	@echo "Rotate any exposed credential FIRST, then rewrite history if needed."
	@echo ""
	@echo "=== Run 'make shell' for the full remediation exercise ==="

shell:
	docker compose exec lab bash
