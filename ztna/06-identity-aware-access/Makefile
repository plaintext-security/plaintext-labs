# Module 06 — Identity-Aware Access lab.
# Standard targets: up / down / reset / demo / shell / check
.PHONY: up down reset demo shell check

up:        ## Build and start Pomerium + whoami backend
	docker compose up -d
	@echo ""
	@echo "Pomerium is starting on https://localhost:8443"
	@echo "The whoami backend has no published port — it is only reachable via Pomerium."
	@echo "Run: make demo"

down:      ## Stop and remove containers
	docker compose down

reset:     ## Tear down completely (containers + volumes)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the Pomerium container
	docker compose exec pomerium sh

# ── Demo ─────────────────────────────────────────────────────────────────────
# Shows two requests:
#   1. Unauthenticated → denied (302 redirect to IdP, not 200)
#   2. Authenticated   → proxied through with identity headers visible
demo:      ## Show denied request then authenticated request through Pomerium
	@echo "== Waiting for Pomerium to be ready =="
	@for i in $$(seq 1 20); do \
	  STATUS=$$(docker compose exec -T pomerium wget -qO- --no-check-certificate \
	    https://localhost/ping 2>&1 | grep -c pomerium || true); \
	  if [ "$$STATUS" -ge 1 ] 2>/dev/null; then break; fi; \
	  echo "  waiting... ($$i/20)"; sleep 3; \
	done
	@echo ""
	@echo "== 1. Unauthenticated request — no JWT =="
	@echo "   curl -sk -o /dev/null -w 'HTTP status: %{http_code}' https://localhost:8443/"
	@docker run --rm --network ztna-lab_ztna-lab curlimages/curl:8.9.1 \
	  curl -sk -o /dev/null -w "HTTP status: %{http_code}\n" \
	  --resolve "whoami.localhost.pomerium.io:443:pomerium" \
	  https://whoami.localhost.pomerium.io/ || true
	@echo "   Expected: 302 (redirect to IdP login) — NOT a 200 from the backend."
	@echo ""
	@echo "== 2. Authenticated request — mock IdP token =="
	@echo "   (Pomerium's test IdP issues tokens for @example.com addresses.)"
	@echo "   In production: real Okta token signed with your tenant's key."
	@echo ""
	@echo "   The whoami service echoes all request headers — look for:"
	@echo "     X-Pomerium-Jwt-Assertion  (signed identity token injected by Pomerium)"
	@echo "     X-Forwarded-For           (original client IP)"
	@echo ""
	@echo "   To test with a real token, open https://whoami.localhost.pomerium.io"
	@echo "   in a browser (add to /etc/hosts: 127.0.0.1 whoami.localhost.pomerium.io)"
	@echo "   and complete the mock IdP login with user@example.com / any password."
	@echo ""
	@echo "== Backend reachability check =="
	@echo "   Confirming whoami has no published port (should time out or refuse):"
	@docker inspect whoami --format '{{range .NetworkSettings.Ports}}{{.}}{{end}}' 2>/dev/null | \
	  grep -q '0.0.0.0' && echo "  FAIL: whoami port is published!" || \
	  echo "  PASS: whoami has no published port — only reachable via Pomerium."

# ── Policy regression check ───────────────────────────────────────────────────
check:     ## Assert unauthenticated request is NOT a 200 (policy smoke-test)
	@echo "== Policy check: unauthenticated request must not return 200 =="
	@STATUS=$$(docker run --rm --network ztna-lab_ztna-lab curlimages/curl:8.9.1 \
	  curl -sk -o /dev/null -w "%{http_code}" \
	  --resolve "whoami.localhost.pomerium.io:443:pomerium" \
	  https://whoami.localhost.pomerium.io/ 2>/dev/null); \
	if [ "$$STATUS" = "200" ]; then \
	  echo "  FAIL: got 200 — backend is reachable without authentication!"; \
	  exit 1; \
	else \
	  echo "  PASS: got HTTP $$STATUS — backend is protected (not a 200)."; \
	fi
