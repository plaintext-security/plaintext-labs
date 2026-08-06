# Module 02 — Identity as the Control Plane lab.
# Standard targets: up / down / reset / demo.
# Recipes use bash features (substring expansion ${VAR:0:80}); force bash so they
# don't break under dash, which is /bin/sh on Debian/Ubuntu CI runners.
SHELL := /bin/bash
.PHONY: up down reset demo

KEYCLOAK_URL = http://localhost:8080
REALM        = corp
CLIENT_ID    = corp-app
CLIENT_SECRET = corp-app-secret
TOKEN_URL    = $(KEYCLOAK_URL)/realms/$(REALM)/protocol/openid-connect/token

up:    ## Start Keycloak with the Corp realm pre-loaded
	@# --force-recreate so a container that crashed on a previous boot (e.g. a
	@# transient hostname-resolution failure in H2 startup) is replaced with a
	@# fresh one instead of merely restarted — a plain `up` restarts the dead
	@# container and would loop here forever.
	docker compose up -d --force-recreate --remove-orphans
	@echo "Waiting for Keycloak + the corp realm to be ready (realm import + boot can take ~60s)..."
	@# Probe the actual token endpoint (from the host, which has curl) until it issues a
	@# token — this is exactly what `make demo` does, so it guarantees users/clients are
	@# fully imported, not just that the realm responds. Bounded so CI fails fast.
	@i=0; until curl -sf -X POST $(TOKEN_URL) \
		-d "grant_type=password" -d "client_id=$(CLIENT_ID)" -d "client_secret=$(CLIENT_SECRET)" \
		-d "username=analyst" -d "password=analyst123" -d "scope=openid" 2>/dev/null | grep -q access_token; do \
		i=$$((i+1)); \
		if [ $$i -gt 100 ]; then echo ""; echo "Keycloak token endpoint did not become ready in time; recent logs:"; docker compose logs --tail 30 keycloak; exit 1; fi; \
		printf '.'; sleep 3; \
	done
	@echo ""
	@echo "Keycloak is ready."
	@echo "  Admin console : http://localhost:8080/admin  (admin / admin)"
	@echo "  Corp realm: http://localhost:8080/realms/corp"

down:  ## Stop Keycloak
	docker compose down

reset: ## Tear down completely (container + volumes)
	docker compose down --rmi local --volumes --remove-orphans

demo:  ## Walk the full OIDC flow: get a JWT for analyst + admin, decode claims
	@echo "============================================================"
	@echo "  Lab 02 — OIDC Token Demo: Corp realm"
	@echo "============================================================"
	@echo ""
	@echo "--- Step 1: Obtain access token for 'analyst' ---"
	@ANALYST_TOKEN=$$(curl -sf -X POST $(TOKEN_URL) \
		-d "grant_type=password" \
		-d "client_id=$(CLIENT_ID)" \
		-d "client_secret=$(CLIENT_SECRET)" \
		-d "username=analyst" \
		-d "password=analyst123" \
		-d "scope=openid" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])"); \
	echo "Raw token (truncated): $${ANALYST_TOKEN:0:80}..."; \
	echo ""; \
	echo "--- Decoded payload (analyst) ---"; \
	echo "$$ANALYST_TOKEN" | python3 -c "\
import sys, base64, json; \
t = sys.stdin.read().strip().split('.')[1]; \
pad = t + '==' * (4 - len(t) % 4); \
print(json.dumps(json.loads(base64.urlsafe_b64decode(pad).decode()), indent=2))"
	@echo ""
	@echo "--- Step 2: Obtain access token for 'admin' ---"
	@ADMIN_TOKEN=$$(curl -sf -X POST $(TOKEN_URL) \
		-d "grant_type=password" \
		-d "client_id=$(CLIENT_ID)" \
		-d "client_secret=$(CLIENT_SECRET)" \
		-d "username=admin" \
		-d "password=admin456" \
		-d "scope=openid" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])"); \
	echo "--- Decoded payload (admin) ---"; \
	echo "$$ADMIN_TOKEN" | python3 -c "\
import sys, base64, json; \
t = sys.stdin.read().strip().split('.')[1]; \
pad = t + '==' * (4 - len(t) % 4); \
print(json.dumps(json.loads(base64.urlsafe_b64decode(pad).decode()), indent=2))"
	@echo ""
	@echo "--- Step 3: Fetch realm public key (JWKS endpoint) ---"
	@curl -s $(KEYCLOAK_URL)/realms/$(REALM)/protocol/openid-connect/certs \
		| python3 -c "import sys,json; keys=json.load(sys.stdin)['keys']; [print('Key ID:', k['kid'], '  Alg:', k['alg']) for k in keys]"
	@echo ""
	@echo "--- Step 4: Audience restriction (the 'aud' claim) ---"
	@AUD_TOKEN=$$(curl -sf -X POST $(TOKEN_URL) \
		-d "grant_type=password" \
		-d "client_id=$(CLIENT_ID)" \
		-d "client_secret=$(CLIENT_SECRET)" \
		-d "username=analyst" \
		-d "password=analyst123" \
		-d "scope=openid" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])"); \
	echo "$$AUD_TOKEN" | python3 -c "\
import sys, base64, json; \
p = sys.stdin.read().strip().split('.')[1]; \
claims = json.loads(base64.urlsafe_b64decode(p + '==' * (4 - len(p) % 4)).decode()); \
print('  aud (who may accept this token):', claims.get('aud', '<MISSING — bound to nothing!>')); \
print('  azp (which client requested it):', claims.get('azp')); \
print(''); \
print('  The token is scoped to a SINGLE audience (corp-app). A resource server'); \
print('  that expects a different aud — e.g. corp-api — rejects it, which is what'); \
print('  stops cross-app token replay. That is flight-card #4: one aud, minimal claims.')"
	@echo ""
	@echo "============================================================"
	@echo "  Demo complete. Inspect the claims above."
	@echo "  Compare 'realm_access.roles' between analyst and admin."
	@echo "  Note 'exp' — token expires in 300 seconds (ZT discipline)."
	@echo "  Note 'aud' — token is bound to a single audience, corp-app (Step 4)."
	@echo "============================================================"
