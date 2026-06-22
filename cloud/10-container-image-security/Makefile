# Module 10 — Container & Image Security
# Standard targets: up / down / reset / demo / shell
.PHONY: up down reset demo shell scan-trivy scan-grype sbom harden-verify

IMAGE_VULN  = python:3.8-slim
IMAGE_NODE  = node:14
DOCKERFILE  = data/Dockerfile.bad

up:        ## Pull scanner images and build the lab container
	docker compose up -d --build

down:      ## Stop and remove containers
	docker compose down

reset:     ## Tear down completely — containers, local image, cached volumes
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the lab container (trivy + grype available)
	docker compose exec lab bash

# ── Demo: the worked pipeline ──────────────────────────────────────────────
demo:      ## Run full scan pipeline: trivy + grype on vuln image, trivy config on Dockerfile.bad
	@docker compose exec lab sh -c '\
		echo "=== 1. Trivy: CVE scan of python:3.8-slim (HIGH+CRITICAL) ==="; \
		trivy image --severity HIGH,CRITICAL --exit-code 0 $(IMAGE_VULN); \
		echo; \
		echo "=== 2. Grype: same image — compare counts ==="; \
		grype $(IMAGE_VULN) --fail-on high; \
		echo; \
		echo "=== 3. Trivy: CVE scan of node:14 ==="; \
		trivy image --severity HIGH,CRITICAL --exit-code 0 $(IMAGE_NODE); \
		echo; \
		echo "=== 4. Trivy config: the BAD Dockerfile (root, latest, secrets in ENV) ==="; \
		trivy config /lab/data/Dockerfile.bad; \
		echo; \
		echo "=== 5. Trivy config: the HARDENED Dockerfile — re-scan to prove the fixes ==="; \
		trivy config /lab/data/Dockerfile.fixed; \
		echo; \
		echo "Hardened rebuild: the MEDIUM/HIGH findings (latest tag, no USER, recommends) are gone."; \
		echo "=== Demo complete. See scan-report.md for your findings. ==="'

harden-verify: ## Gate: the hardened Dockerfile must have no MEDIUM+ misconfig (bad fails, fixed passes)
	@echo "== BAD Dockerfile (expect MEDIUM/HIGH failures, non-zero) =="
	-docker compose exec lab trivy config --severity MEDIUM,HIGH,CRITICAL --exit-code 1 /lab/data/Dockerfile.bad
	@echo
	@echo "== HARDENED Dockerfile (expect no MEDIUM+ findings, exit 0) =="
	docker compose exec lab trivy config --severity MEDIUM,HIGH,CRITICAL --exit-code 1 /lab/data/Dockerfile.fixed

# ── Individual scan helpers ─────────────────────────────────────────────────
scan-trivy: ## make scan-trivy IMAGE=<image> — trivy CVE scan
	docker compose exec lab trivy image --severity HIGH,CRITICAL $(IMAGE)

scan-grype: ## make scan-grype IMAGE=<image> — grype CVE scan
	docker compose exec lab grype $(IMAGE)

sbom:      ## Generate a CycloneDX SBOM: make sbom IMAGE=python:3.8-slim
	docker compose exec lab trivy image --format cyclonedx \
		--output /lab/sbom.json $(IMAGE)
	@echo "SBOM written to sbom.json"
