# Module 05 — Intrusion Detection lab.
.PHONY: up down reset shell demo suricata
up:
	docker compose up -d --build
down:
	docker compose down
reset:
	docker compose down --rmi local --volumes --remove-orphans
shell:
	docker compose exec lab bash
demo:
	docker compose run --rm lab python3 parse_alerts.py
# Run Suricata against a local PCAP: PCAP=my.pcap make suricata
suricata:
	docker compose --profile suricata run --rm suricata suricata -r /data/$(PCAP) -l /data/ -S /data/local.rules
