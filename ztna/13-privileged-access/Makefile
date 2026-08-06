# Module 13 — Privileged Access (Teleport Community Edition) lab.
# Standard targets: up / down / reset / demo / shell, plus login / ssh / play /
# deny-role / deny-expired / deny-bypass / tighten / check.
.PHONY: up down reset demo shell login ssh play deny-role deny-expired deny-bypass tighten check

up:     ## Build + start auth/proxy and the node, then bootstrap roles/users/join-token
	docker compose up -d --build
	@echo "Waiting for the auth service to report healthy..."
	@until [ "$$(docker compose ps -q teleport-auth | xargs docker inspect -f '{{.State.Health.Status}}' 2>/dev/null)" = "healthy" ]; do sleep 1; done
	docker compose exec teleport-auth bash /opt/teleport/data/setup.sh
	@echo "Waiting for the node to join..."
	@sleep 5
	@echo "Lab ready. Try:  make login   |   make ssh   |   make demo"

down:   ## Stop and remove containers
	docker compose down

reset:  ## Tear down completely (containers + local image + volumes)
	docker compose down --rmi local --volumes --remove-orphans

shell:  ## Drop into the client container (tsh CLI available)
	docker compose exec client bash

login:  ## Mint alice a short-lived cert and log in (tctl auth sign + tsh login)
	docker compose exec teleport-auth bash /opt/teleport/workload/mint-cert.sh alice 15m
	docker compose exec client bash /opt/teleport/workload/operate.sh alice login
	docker compose exec client bash /opt/teleport/workload/operate.sh alice status

ssh:    ## alice SSHes to app-prod-01 THROUGH THE PROXY — the session is recorded
	docker compose exec client bash /opt/teleport/workload/operate.sh alice ssh "whoami; hostname; echo 'privileged session OK'"

play:   ## List recordings and replay the most recent one — the audit artifact
	docker compose exec client bash /opt/teleport/workload/operate.sh alice recordings
	docker compose exec client bash /opt/teleport/workload/operate.sh alice play-latest

deny-role:      ## Prove a user WITHOUT the right role is denied (mallory)
	docker compose exec teleport-auth bash /opt/teleport/workload/mint-cert.sh mallory 15m
	docker compose exec client bash /opt/teleport/workload/operate.sh mallory login
	-docker compose exec client bash /opt/teleport/workload/operate.sh mallory ssh "whoami"
	@echo "(Expected: access denied — mallory's role has no entry matching app-prod-01's labels.)"

deny-expired:   ## Prove an EXPIRED certificate is denied
	docker compose exec teleport-auth bash /opt/teleport/workload/mint-cert.sh alice 30s alice-short
	@echo "Waiting 35s for the certificate to expire..."
	@sleep 35
	-docker compose exec client bash /opt/teleport/workload/operate.sh alice-short login
	@echo "(Expected: certificate has expired — a valid role doesn't save an expired cert.)"

deny-bypass:    ## Prove a direct connection to the node, skipping the proxy, is refused
	@echo "== app-prod-01 has no listening SSH port; it only dials OUT to the proxy =="
	-docker compose exec client nc -zv -w3 app-prod-01 3022
	@echo "(Expected: connection refused — there is nothing here to bypass into.)"

tighten:        ## Apply the least-privilege version of privileged-ops (Step 5)
	docker compose exec teleport-auth tctl create -f /opt/teleport/data/role-privileged-ops-tightened.yaml --force
	@echo "privileged-ops is now logins=[ubuntu], node_labels={env: production}. Re-run 'make ssh' — alice still works."

check:  ## Assert the deny path: unauthorized denied, no direct bypass (plus the allow anchor)
	bash check-access.sh

demo:   ## Full walkthrough: allowed + recorded session, then both denials
	@echo "============================================================"
	@echo "  Lab 13 — Privileged Access (Teleport Community Edition)"
	@echo "============================================================"
	@$(MAKE) --no-print-directory login
	@echo ""
	@$(MAKE) --no-print-directory ssh
	@echo ""
	@$(MAKE) --no-print-directory play
	@echo ""
	@$(MAKE) --no-print-directory deny-role
	@echo ""
	@$(MAKE) --no-print-directory deny-bypass
	@echo ""
	@echo "============================================================"
	@echo "  A certificate proved identity; the ROLE decided access;"
	@echo "  the PROXY was the only path in. That's the control."
	@echo "============================================================"
