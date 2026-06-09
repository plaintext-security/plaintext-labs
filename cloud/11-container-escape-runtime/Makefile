# Module 11 — Container Escape & Runtime Security
# Standard targets: up / down / reset / demo / shell
.PHONY: up down reset demo shell logs-falco trigger-alert

up:        ## Start the lab: attacker container, target, and Falco sensor
	docker compose up -d --build
	@echo ""
	@echo "Lab is up. Open a second terminal and run: make logs-falco"
	@echo "Then: make shell to enter the attacker container"

down:      ## Stop and remove containers
	docker compose down

reset:     ## Tear down completely — containers, local images, volumes
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Shell into the attacker container (--privileged)
	docker compose exec attacker bash

logs-falco: ## Tail Falco alert output (run in a second terminal)
	docker compose logs -f falco

# ── Demo: runs the full escape + detection scenario ───────────────────────
demo:      ## Demonstrate the escape path and Falco detection end-to-end
	@echo "=== Module 11 Demo: Container Escape + Falco Detection ==="
	@echo ""
	@echo "--- Step 1: Show /etc/passwd write (triggers Falco Rule 1) ---"
	docker compose exec attacker sh -c \
		'echo "# Lab trigger — not a real account" >> /etc/passwd && echo "Written to /etc/passwd"'
	@echo ""
	@echo "--- Step 2: Read the host-side secret via bind mount ---"
	docker compose exec attacker sh -c 'cat /host-secret.txt'
	@echo ""
	@echo "--- Step 3: Show Falco alerts (last 10 lines) ---"
	@docker compose logs --tail=20 falco 2>/dev/null | grep -E '(CRITICAL|WARNING|rule)' || \
		echo "(Falco may need a moment — run 'make logs-falco' in a second terminal for live output)"
	@echo ""
	@echo "=== Demo complete. See escape-report.md for your writeup. ==="

# ── Individual helpers ────────────────────────────────────────────────────
trigger-alert: ## Manually trigger the /etc/passwd write alert
	docker compose exec attacker sh -c 'echo "# trigger" >> /etc/passwd'
