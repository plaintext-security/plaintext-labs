# Module 06 — PKI & Certificate Management
# Standard targets: up / down / reset / demo / shell

.PHONY: up down reset demo shell

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

demo:
	@echo "=== Module 06 — PKI & Certificate Management Demo ==="
	@echo ""
	@echo "--- Initialising Corp Private CA and issuing a leaf certificate ---"
	docker compose exec lab bash /lab/data/init-ca.sh
	@echo ""
	@echo "--- Leaf certificate fields (SAN, validity, basicConstraints) ---"
	docker compose exec lab bash -c '\
		echo "Subject Alternative Names:"; \
		openssl x509 -in /tmp/leaf.crt -noout -ext subjectAltName 2>/dev/null; \
		echo ""; \
		echo "Validity:"; \
		openssl x509 -in /tmp/leaf.crt -noout -dates; \
		echo ""; \
		echo "CA flag (basicConstraints):"; \
		openssl x509 -in /tmp/leaf.crt -noout -text | grep -A2 "Basic Constraints" || \
		echo "  (no CA basicConstraints — correct: a leaf certificate is NOT a CA)"'
	@echo ""
	@echo "=== Run 'make shell' for the full revocation and OCSP exercises ==="

shell:
	docker compose exec lab bash
