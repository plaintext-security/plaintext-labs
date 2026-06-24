# Module 09 — Email Authentication
# Standard targets: up / down / reset / demo / shell

.PHONY: up down reset demo shell

DNS_CONTAINER=email-auth-dns

up:
	docker compose up -d --build

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

demo:
	@echo "=== Module 09 — Email Authentication Demo ==="
	@echo ""
	@echo "--- Querying SPF record for corp-fictional.com ---"
	docker compose exec dns bash -c '\
		dig @127.0.0.1 TXT corp-fictional.com +short 2>/dev/null | grep spf || \
		echo "SPF: v=spf1 ip4:203.0.113.10 ip4:203.0.113.20 include:sendgrid.net ~all"'
	@echo ""
	@echo "  FINDING: ~all (softfail) should be -all (hardfail)"
	@echo ""
	@echo "--- Querying DKIM record (selector: corp2024) ---"
	docker compose exec dns bash -c '\
		dig @127.0.0.1 TXT corp2024._domainkey.corp-fictional.com +short 2>/dev/null | head -3 || \
		echo "DKIM: v=DKIM1; k=rsa; p=MIIBIjAN..."'
	@echo ""
	@echo "--- Querying DMARC record ---"
	docker compose exec dns bash -c '\
		dig @127.0.0.1 TXT _dmarc.corp-fictional.com +short 2>/dev/null || \
		echo "DMARC: v=DMARC1; p=none; adkim=r; aspf=r; pct=100"'
	@echo ""
	@echo "  FINDINGS:"
	@echo "  - p=none: no enforcement (messages are not rejected or quarantined)"
	@echo "  - adkim=r: relaxed alignment (less strict)"
	@echo "  - missing rua=: no aggregate reporting configured"
	@echo ""
	@echo "--- Reading the full record analysis ---"
	docker compose exec dns bash -c 'cat /lab/data/dns-records.txt | grep -A5 "FINDINGS"'
	@echo ""
	@echo "=== Run 'make shell' for the full audit and validation exercise ==="

shell:
	docker compose exec lab bash
