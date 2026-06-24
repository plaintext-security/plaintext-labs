# Module 05 — Intrusion Detection lab.
.PHONY: up down reset shell demo suricata fetch-data
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

# Fetch the real MTA.net capture and run Suricata over it (see data/PROVENANCE.md).
PCAP_URL ?= https://www.malware-traffic-analysis.net/2024/12/17/2024-12-17-SmartApeSG-to-NetSupport-RAT.pcap.zip
fetch-data: ## Download the real MTA.net PCAP and run Suricata over it → data/eve.json
	@echo "Downloading $(PCAP_URL) ..."
	curl -fL -o data/capture.pcap.zip "$(PCAP_URL)"
	# MTA.net zips are password-protected; password is the standard "infected".
	cd data && unzip -P infected -o capture.pcap.zip && mv *.pcap capture.pcap
	# Update the ET Open ruleset, then run Suricata over the capture → data/eve.json.
	docker compose --profile suricata run --rm suricata suricata-update
	PCAP=capture.pcap $(MAKE) suricata
	@echo "Done. Real eve.json is in data/ — analyze with: python3 parse_alerts.py data/eve.json"
