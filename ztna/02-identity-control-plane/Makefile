# Module 02 — Identity as the Control Plane lab.
# Standard targets: up / down / reset / demo.
.PHONY: up down reset demo

KEYCLOAK_URL = http://localhost:8080
REALM        = meridian
CLIENT_ID    = meridian-app
CLIENT_SECRET = meridian-app-secret
TOKEN_URL    = $(KEYCLOAK_URL)/realms/$(REALM)/protocol/openid-connect/token

up:    ## Start Keycloak with the Meridian realm pre-loaded
	docker compose up -d
	@echo "Waiting for Keycloak to be ready..."
	@until docker compose exec keycloak curl -sf http://localhost:8080/realms/meridian > /dev/null 2>&1; do \
		printf '.'; sleep 3; \
	done
	@echo ""
	@echo "Keycloak is ready."
	@echo "  Admin console : http://localhost:8080/admin  (admin / admin)"
	@echo "  Meridian realm: http://localhost:8080/realms/meridian"

down:  ## Stop Keycloak
	docker compose down

reset: ## Tear down completely (container + volumes)
	docker compose down --rmi local --volumes --remove-orphans

demo:  ## Walk the full OIDC flow: get a JWT for analyst + admin, decode claims
	@echo "============================================================"
	@echo "  Lab 02 — OIDC Token Demo: Meridian realm"
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
	@echo "============================================================"
	@echo "  Demo complete. Inspect the claims above."
	@echo "  Compare 'realm_access.roles' between analyst and admin."
	@echo "  Note 'exp' — token expires in 300 seconds (ZT discipline)."
	@echo "============================================================"
