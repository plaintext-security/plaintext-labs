# Module 08 — Policy as Code lab.
# Requires: docker
# Standard targets: up / down / reset / demo / shell / eval / test / ci
.PHONY: up down reset demo shell eval test ci

up:        ## Start OPA server and runner container
	docker compose up -d
	@echo "OPA server running on http://localhost:8181"
	@echo "Run: make demo"

down:      ## Stop containers
	docker compose down

reset:     ## Tear down completely
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the OPA runner container
	docker compose exec lab sh

# ── Demo ─────────────────────────────────────────────────────────────────────
demo:      ## Run all policy scenarios — allow and deny cases for both policies
	@echo "========================================================"
	@echo "  SCENARIO 1: Data Access Policy (by role)"
	@echo "========================================================"
	@echo ""
	@echo "-- Case A: analyst READ (expect: allow=true) --"
	docker compose run --rm lab opa eval \
	  --input /lab/data/inputs/analyst-read.json \
	  --data /lab/data/policies/data-access.rego \
	  "data.meridian.access.allow"
	@echo ""
	@echo "-- Case B: analyst WRITE (expect: allow=false, deny=true) --"
	docker compose run --rm lab opa eval \
	  --input /lab/data/inputs/analyst-write.json \
	  --data /lab/data/policies/data-access.rego \
	  "data.meridian.access.allow"
	docker compose run --rm lab opa eval \
	  --input /lab/data/inputs/analyst-write.json \
	  --data /lab/data/policies/data-access.rego \
	  "data.meridian.access.deny"
	@echo ""
	@echo "-- Case C: admin WRITE (expect: allow=true) --"
	docker compose run --rm lab opa eval \
	  --input /lab/data/inputs/admin-write.json \
	  --data /lab/data/policies/data-access.rego \
	  "data.meridian.access.allow"
	@echo ""
	@echo "-- Case D: service_account WRITE (expect: allow=false, deny=true) --"
	docker compose run --rm lab opa eval \
	  --input /lab/data/inputs/service-account-write.json \
	  --data /lab/data/policies/data-access.rego \
	  "data.meridian.access.allow"
	docker compose run --rm lab opa eval \
	  --input /lab/data/inputs/service-account-write.json \
	  --data /lab/data/policies/data-access.rego \
	  "data.meridian.access.deny"
	@echo ""
	@echo "========================================================"
	@echo "  SCENARIO 2: Kubernetes Admission — no root pods"
	@echo "========================================================"
	@echo ""
	@echo "-- Case E: pod with runAsUser=0 (expect: deny=true) --"
	docker compose run --rm lab opa eval \
	  --input /lab/data/inputs/pod-root.json \
	  --data /lab/data/policies/k8s-admission.rego \
	  "data.k8s.admission.deny"
	@echo ""
	@echo "-- Case F: pod with no runAsUser (expect: deny=true) --"
	docker compose run --rm lab opa eval \
	  --input /lab/data/inputs/pod-no-user.json \
	  --data /lab/data/policies/k8s-admission.rego \
	  "data.k8s.admission.deny"
	@echo ""
	@echo "-- Case G: pod with runAsUser=1000 (expect: deny=false) --"
	docker compose run --rm lab opa eval \
	  --input /lab/data/inputs/pod-nonroot.json \
	  --data /lab/data/policies/k8s-admission.rego \
	  "data.k8s.admission.deny"

# ── One-off eval (make eval POLICY=... INPUT=...) ──────────────────────────
eval:      ## Eval a policy against an input: make eval POLICY=<path> INPUT=<path>
	docker compose run --rm lab opa eval \
	  --input /lab/$(INPUT) \
	  --data /lab/$(POLICY) \
	  "data"

# ── Run all OPA tests ─────────────────────────────────────────────────────
test:      ## Run opa test over all policies in data/policies/
	@echo "== Running OPA policy tests =="
	docker compose run --rm lab opa test /lab/data/policies/ -v

# ── CI target ──────────────────────────────────────────────────────────────
ci:        ## Run opa test (used in CI / GitHub Actions)
	docker compose run --rm --no-deps lab opa test /lab/data/policies/ -v
