# Module 04 — Network Monitoring lab.
.PHONY: up down reset shell demo zeek fetch-data
up:
	docker compose up -d --build
down:
	docker compose down
reset:
	docker compose down --rmi local --volumes --remove-orphans
shell:
	docker compose exec lab bash
demo:
	docker compose run --rm lab python3 analyze.py
# Run Zeek against a local PCAP: PCAP=my.pcap make zeek
zeek:
	docker compose --profile zeek run --rm zeek zeek -C -r /lab/$(PCAP)

# Fetch the real MTA.net capture and rebuild the Zeek logs from it (see data/PROVENANCE.md).
PCAP_URL ?= https://www.malware-traffic-analysis.net/2024/12/17/2024-12-17-SmartApeSG-to-NetSupport-RAT.pcap.zip
fetch-data: ## Download the real MTA.net PCAP and run Zeek over it → data/zeek/*.log
	@echo "Downloading $(PCAP_URL) ..."
	curl -fL -o data/capture.pcap.zip "$(PCAP_URL)"
	# MTA.net zips are password-protected; password is the standard "infected".
	cd data && unzip -P infected -o capture.pcap.zip && mv *.pcap capture.pcap
	# Run Zeek over the capture to regenerate conn.log, dns.log, http.log, etc.
	PCAP=../data/capture.pcap $(MAKE) zeek
	@echo "Done. Real Zeek logs are in data/zeek/ — analyze with: python3 analyze.py data/zeek"
