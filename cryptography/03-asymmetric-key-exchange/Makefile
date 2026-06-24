# Module 03 — Asymmetric & Key Exchange
# Standard targets: up / down / reset / demo / shell

.PHONY: up down reset demo shell

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

demo:
	@echo "=== Module 03 — Asymmetric & Key Exchange Demo ==="
	@echo ""
	@echo "--- RSA-2048 key generation ---"
	docker compose exec lab bash -c '\
		time openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 \
		  -out /tmp/rsa-priv.pem 2>/dev/null && \
		openssl pkey -in /tmp/rsa-priv.pem -pubout -out /tmp/rsa-pub.pem 2>/dev/null && \
		echo "RSA-2048 private key size: $$(wc -c < /tmp/rsa-priv.pem) bytes" && \
		echo "RSA-2048 public key size:  $$(wc -c < /tmp/rsa-pub.pem) bytes"'
	@echo ""
	@echo "--- EC P-256 key generation ---"
	docker compose exec lab bash -c '\
		time openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 \
		  -out /tmp/ec-priv.pem 2>/dev/null && \
		openssl pkey -in /tmp/ec-priv.pem -pubout -out /tmp/ec-pub.pem 2>/dev/null && \
		echo "EC P-256 private key size: $$(wc -c < /tmp/ec-priv.pem) bytes" && \
		echo "EC P-256 public key size:  $$(wc -c < /tmp/ec-pub.pem) bytes"'
	@echo ""
	@echo "--- Sign and verify with ECDSA ---"
	docker compose exec lab bash -c '\
		echo "Corp payroll batch authorisation" > /tmp/msg.txt && \
		openssl pkeyutl -sign -inkey /tmp/ec-priv.pem -in /tmp/msg.txt \
		  -out /tmp/sig.bin 2>/dev/null && \
		openssl pkeyutl -verify -pubin -inkey /tmp/ec-pub.pem \
		  -sigfile /tmp/sig.bin -in /tmp/msg.txt 2>/dev/null && \
		echo "Signature verified successfully"'
	@echo ""
	@echo "--- X25519 ECDH key exchange (Alice and Bob) ---"
	docker compose exec lab bash -c '\
		openssl genpkey -algorithm X25519 -out /tmp/alice-priv.pem 2>/dev/null && \
		openssl pkey -in /tmp/alice-priv.pem -pubout -out /tmp/alice-pub.pem 2>/dev/null && \
		openssl genpkey -algorithm X25519 -out /tmp/bob-priv.pem 2>/dev/null && \
		openssl pkey -in /tmp/bob-priv.pem -pubout -out /tmp/bob-pub.pem 2>/dev/null && \
		alice_secret=$$(openssl pkeyutl -derive -inkey /tmp/alice-priv.pem -peerkey /tmp/bob-pub.pem 2>/dev/null | xxd -p | tr -d "\n") && \
		bob_secret=$$(openssl pkeyutl -derive -inkey /tmp/bob-priv.pem -peerkey /tmp/alice-pub.pem 2>/dev/null | xxd -p | tr -d "\n") && \
		echo "Alice computed: $${alice_secret:0:32}..." && \
		echo "Bob computed:   $${bob_secret:0:32}..." && \
		[ "$$alice_secret" = "$$bob_secret" ] && \
		echo "Shared secrets MATCH — DH key exchange successful!" || \
		echo "ERROR: Shared secrets do not match"'
	@echo ""
	@echo "=== Run 'make shell' for the full benchmark and forward secrecy exercises ==="

shell:
	docker compose exec lab bash
