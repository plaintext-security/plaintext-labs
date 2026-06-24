.PHONY: up down reset demo shell pcap fetch-data

up:
	docker compose up -d --build
	@echo "Container ready. Run 'make fetch-data' for the REAL Redline PCAP,"
	@echo "or 'make pcap' for the synthetic fallback, then 'make demo'."

# fetch-data — download the REAL Redline Stealer infection PCAP (idempotent).
# Source: Malware-Traffic-Analysis.net, 2024-10-23. The zip is PASSWORD-PROTECTED
# (password 'infected', per the site's About page) and contains a real malware
# capture, so we DOWNLOAD it but DO NOT unzip — the learner unzips with the
# password, then renames the .pcap to data/capture.pcap. See PROVENANCE.md.
MTA_PCAP_URL  ?= https://www.malware-traffic-analysis.net/2024/10/23/2024-10-23-Redline-Stealer-infection-traffic.pcap.zip
MTA_IOCS_URL  ?= https://www.malware-traffic-analysis.net/2024/10/23/2024-10-23-IOCs-for-Redline-Stealer-infection.txt.zip
fetch-data:
	@mkdir -p data
	@if [ -f data/2024-10-23-Redline-Stealer-infection-traffic.pcap.zip ]; then \
		echo "PCAP zip already present — skipping download."; \
	else \
		echo "Downloading real Redline Stealer PCAP zip (NOT unzipping — password-protected)..."; \
		curl -fsSL -o data/2024-10-23-Redline-Stealer-infection-traffic.pcap.zip "$(MTA_PCAP_URL)"; \
		curl -fsSL -o data/2024-10-23-IOCs-for-Redline-Stealer-infection.txt.zip   "$(MTA_IOCS_URL)" || true; \
		echo "Saved to data/. Unzip with password 'infected', then:"; \
		echo "  mv 2024-10-23-Redline-Stealer-infection-traffic.pcap data/capture.pcap"; \
		echo "Record the SHA-256 in PROVENANCE.md."; \
	fi

pcap:
	@docker compose exec lab python3 /scripts/gen_pcap.py
	@echo "capture.pcap written to data/"

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans
	rm -f data/capture.pcap

demo:
	@if [ ! -f data/capture.pcap ]; then \
		echo "Generating capture.pcap first..."; \
		docker compose exec lab python3 /scripts/gen_pcap.py; \
	fi
	docker compose exec lab sh /scripts/demo.sh

shell:
	docker compose exec lab bash
