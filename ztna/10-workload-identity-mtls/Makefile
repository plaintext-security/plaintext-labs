# Module 10 — Workload Identity & mTLS (SPIFFE/SPIRE) lab.
# Standard targets: up / down / reset / demo / shell, plus mtls / deny / check.
.PHONY: up down reset demo shell mtls deny check

up:     ## Build + start SPIRE (server, agent), bootstrap entries, and the workloads
	docker compose up -d --build
	@echo "Waiting for the agent to attest and issue SVIDs..."
	@sleep 8
	@echo "Lab ready. Try:  make mtls   |   make deny   |   make demo"

down:   ## Stop and remove containers
	docker compose --profile deny down

reset:  ## Tear down completely (containers + local image + volumes)
	docker compose --profile deny down --rmi local --volumes --remove-orphans

shell:  ## Drop into the client workload (spire-agent CLI + openssl available)
	docker compose exec client bash

mtls:   ## Client fetches its SVID and makes a mutual-TLS call to the backend
	docker compose exec client /opt/spire/workload/connect.sh

deny:   ## Prove an unregistered workload ("rogue") is refused an identity
	docker compose --profile deny up -d rogue
	@sleep 2
	@echo "== rogue asks the Workload API for an SVID (no matching entry exists) =="
	-docker compose exec rogue spire-agent api fetch x509 -socketPath /run/spire/sockets/agent.sock
	@echo ""
	@echo "(Expected: 'no identity issued' / no SVID — identity, not network position, grants access.)"

check:  ## Assert registered workloads get the right SVID and rogue gets none
	bash check_identity.sh

demo:   ## Full walkthrough: registered mTLS succeeds, then the unregistered deny
	@echo "============================================================"
	@echo "  Lab 10 — Workload Identity & mTLS (SPIFFE/SPIRE)"
	@echo "============================================================"
	@echo ""
	@echo "== Registration entries the server issued =="
	-docker compose exec spire-server spire-server entry show -socketPath /tmp/spire-server/private/api.sock
	@echo ""
	@echo "== Part 1: client -> backend with MUTUAL TLS (both present an SVID) =="
	-docker compose exec client /opt/spire/workload/connect.sh
	@echo ""
	@echo "== Part 2: an UNREGISTERED workload is refused an identity =="
	@$(MAKE) --no-print-directory deny
	@echo ""
	@echo "============================================================"
	@echo "  Identity — not network position — is what granted access."
	@echo "============================================================"
