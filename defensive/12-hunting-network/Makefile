# Module 12 — Network Hunting lab.
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
	docker compose run --rm lab python3 beacon_hunt.py

# Run Zeek against a local PCAP: PCAP=my.pcap make zeek
zeek:
	docker compose --profile zeek run --rm zeek zeek -C -r /lab/$(PCAP)

# Fetch the real MTA.net capture and rebuild conn.log from it (see data/PROVENANCE.md).
# The default capture (NetSupport RAT) contains HTTP C2 callbacks to hunt for.
PCAP_URL ?= https://www.malware-traffic-analysis.net/2024/12/17/2024-12-17-SmartApeSG-to-NetSupport-RAT.pcap.zip
fetch-data: ## Download the real MTA.net PCAP and run Zeek over it → data/zeek/conn.log
	@echo "Downloading $(PCAP_URL) ..."
	curl -fL -o data/capture.pcap.zip "$(PCAP_URL)"
	# MTA.net zips are password-protected; password is the standard "infected".
	cd data && unzip -P infected -o capture.pcap.zip && mv *.pcap capture.pcap
	# Run Zeek in data/zeek/ so conn.log lands where beacon_hunt.py reads it.
	cd data/zeek && docker compose -f ../../docker-compose.yml --profile zeek run --rm \
		-w /lab/data/zeek zeek zeek -C -r /lab/data/capture.pcap
	@echo "Done. Real conn.log is in data/zeek/ — hunt with: python3 beacon_hunt.py data/zeek"
