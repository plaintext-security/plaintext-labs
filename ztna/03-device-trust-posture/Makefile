# Module 03 — Device Trust & Posture lab.
# Standard targets: up / down / reset / demo.
.PHONY: up down reset demo

up:    ## Start headscale + target-service + node containers
	docker compose up -d
	@echo "Waiting for headscale to be ready..."
	@until docker compose exec headscale headscale version > /dev/null 2>&1; do \
		printf '.'; sleep 2; \
	done
	@echo ""
	@echo "headscale is ready."
	@echo "  Headscale admin API : http://localhost:8088"
	@echo "  Target service      : NOT exposed on host (only reachable via mesh)"
	@echo ""
	@echo "Run 'make demo' to register a node and walk the access-control demonstration."

down:  ## Stop all containers
	docker compose down

reset: ## Tear down completely (containers + volumes + images)
	docker compose down --rmi local --volumes --remove-orphans

demo:  ## Register a node, show device list, demonstrate access control
	@echo "============================================================"
	@echo "  Lab 03 — Device Trust Demo: headscale + WireGuard"
	@echo "============================================================"
	@echo ""
	@echo "--- Step 1: Create a headscale user (namespace) for Meridian ---"
	docker compose exec headscale headscale users create meridian 2>/dev/null || true
	@echo ""
	@echo "--- Step 2: Create a pre-authentication key ---"
	@AUTHKEY=$$(docker compose exec -T headscale headscale preauthkeys create --user meridian --reusable --expiration 1h | tail -1 | tr -d '[:space:]'); \
	echo "Pre-auth key: $$AUTHKEY"; \
	echo ""; \
	echo "--- Step 3: List registered nodes (before registration) ---"; \
	docker compose exec headscale headscale nodes list; \
	echo ""; \
	echo "--- Step 4: Access from registered node (direct network — simulating mesh) ---"; \
	docker compose exec node wget -qO- http://target-service/ 2>/dev/null || \
		echo "(wget not available; install with: apk add wget curl)"; \
	docker compose exec node sh -c 'apk add -q curl 2>/dev/null; curl -sf http://target-service/' || true
	@echo ""
	@echo "--- Step 5: Show headscale node list ---"
	docker compose exec headscale headscale nodes list
	@echo ""
	@echo "--- Step 6: Show device posture policy ---"
	@echo "Open data/device-posture-policy.json to see the Meridian posture requirements."
	@echo "Open data/headscale-acl.yaml to see the ACL that enforces device tags."
	@echo ""
	@echo "============================================================"
	@echo "  Demo complete."
	@echo ""
	@echo "  Key question: what happens if a container WITHOUT a registered"
	@echo "  WireGuard keypair tries to reach target-service?"
	@echo ""
	@echo "  Try: docker run --rm --network ztna-03_ztna-net \\"
	@echo "         curlimages/curl:8.9.1 curl -s --max-time 5 http://target-service/"
	@echo "  (Should time out or be refused — no mesh enrollment = no access)"
	@echo "============================================================"
