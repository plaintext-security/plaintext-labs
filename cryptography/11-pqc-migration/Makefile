# Module 11 — PQC Migration lab.
# Standard targets: up / down / reset / shell / demo, plus the migration verbs:
# inventory / migrate / verify / rollback.
#
# NOTE FOR MAINTAINERS: the modern client + server depend on OpenSSL >= 3.5 for
# native X25519MLKEM768 (base image alpine:3.22). A runner whose pulled image
# lacks ML-KEM is the exact silent-fallback failure this lab teaches — see
# VALIDATION.md before adding a .ci-demo marker.
.PHONY: up down reset shell demo inventory migrate verify rollback verify-modern verify-legacy

up:        ## Build and start the server + modern + legacy clients
	docker compose up -d --build
	@echo "Server on classical baseline. Try: make inventory"

down:      ## Stop and remove the containers
	docker compose down

reset:     ## Tear down completely (containers + local images + volumes)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the MODERN client (override: make shell C=legacy)
	docker compose exec $(or $(C),modern) bash

# --- Baseline crypto inventory (read the live handshake) ------------------
inventory: ## Print what each client negotiates against the service today
	@echo "== MODERN client inventory =="
	-docker compose exec -e ROLE=modern modern bash /lab/data/crypto-inventory.sh server:443
	@echo
	@echo "== LEGACY client inventory =="
	-docker compose exec -e ROLE=legacy legacy bash /lab/data/crypto-inventory.sh server:443

# --- Migration mechanism (additive; idempotent; re-runnable) --------------
migrate:   ## Add X25519MLKEM768 in front of classical groups, reload nginx (no downtime)
	docker compose exec server sh -c 'cp /lab/data/nginx-hybrid.conf /etc/nginx/http.d/default.conf && nginx -t && nginx -s reload'
	@echo "Migrated: hybrid X25519MLKEM768 offered, classical fallback retained."

rollback:  ## Restore the classical-only group list, reload nginx
	docker compose exec server sh -c 'cp /lab/data/nginx-classical.conf /etc/nginx/http.d/default.conf && nginx -t && nginx -s reload'
	@echo "Rolled back: classical-only groups restored."

# --- The before/after gate (fail-closed) ----------------------------------
verify-modern:
	docker compose exec -e ROLE=modern modern bash /lab/data/handshake-check.sh server:443

verify-legacy:
	docker compose exec -e ROLE=legacy legacy bash /lab/data/handshake-check.sh server:443

verify: verify-modern verify-legacy  ## Assert: modern=hybrid, legacy=classical, both 200 (fail-closed)
	@echo "verify: both clients passed."

# --- Worked example (the "what good looks like" demo) ---------------------
# Deterministic before/after: prove the modern client is on classical BEFORE,
# migrate, then prove it is on hybrid AFTER while the legacy client is unmoved.
demo:      ## Worked example: rollback -> show modern on classical -> migrate -> show hybrid + interop
	@echo "== 0. Reset to classical baseline =="
	-$(MAKE) --no-print-directory rollback
	@echo
	@echo "== 1. BEFORE: inventory (modern + legacy both classical) =="
	-$(MAKE) --no-print-directory inventory
	@echo
	@echo "== 2. BEFORE: verify gate should FAIL for modern (still classical) =="
	-docker compose exec -e ROLE=modern modern bash /lab/data/handshake-check.sh server:443 || echo "(expected: modern not yet on hybrid)"
	@echo
	@echo "== 3. MIGRATE (add hybrid in front, keep classical) =="
	$(MAKE) --no-print-directory migrate
	@echo
	@echo "== 4. AFTER: verify gate (modern=HYBRID, legacy=CLASSICAL, both 200) =="
	$(MAKE) --no-print-directory verify
	@echo
	@echo "== 5. AFTER: inventory proves the negotiated group differs =="
	$(MAKE) --no-print-directory inventory
	@echo
	@echo "Demo complete: modern negotiates X25519MLKEM768; legacy still classical; interop preserved."
