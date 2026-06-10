# Module 08 — Patch & Vulnerability Management
# Standard targets: up / down / reset / demo / shell

.PHONY: up down reset demo shell

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

demo:
	@echo "=== Module 08 — Patch & Vulnerability Management Demo ==="
	@echo ""
	@echo "--- Step 1: osquery package inventory ---"
	docker compose exec lab bash -c \
		'osqueryi --json "SELECT name, version FROM deb_packages ORDER BY name LIMIT 15" 2>/dev/null | python3 /lab/demo/pkg_inventory.py'
	@echo ""
	@echo "--- Step 2: grype CVE scan (this may take a moment) ---"
	docker compose exec lab bash -c \
		'grype dir:/ --scope all-layers --quiet 2>/dev/null | grep -v "^No vulnerabilities found" | head -30 || echo "(grype scan complete — see output above)"'
	@echo ""
	@echo "--- Step 3: Severity summary ---"
	docker compose exec lab bash -c \
		'grype dir:/ --scope all-layers -o json --quiet 2>/dev/null | python3 /lab/demo/severity_summary.py 2>/dev/null || echo "(install grype to see CVE breakdown)"'
	@echo ""
	@echo "=== Run 'make shell' for interactive analysis ==="

shell:
	docker compose exec lab bash
