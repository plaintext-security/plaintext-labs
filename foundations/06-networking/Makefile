.PHONY: up down reset shell demo fetch-data

# Fetch a REAL malware C2 capture to hunt in (upgrade from the bundled synthetic
# beacon). Source: Malware-Traffic-Analysis.net — a real RAT C2 traffic-analysis
# exercise. See data/PROVENANCE.md for the exact post and why this step is
# deliberately manual.
#
# IMPORTANT: MTA.net pcaps ship as PASSWORD-PROTECTED zips ON PURPOSE — the
# archives contain live malware artifacts and the password (on the site's
# "about" page, shown as an image to defeat scrapers) gates auto-extraction.
# So this target DOWNLOADS the zip (via the shared dataset cache, lib/fetch.sh —
# cached ONCE, still password-protected) but does NOT unzip it — you supply the
# password yourself, which is the correct, safety-aware workflow.
# NOTE (runner-validation): hits the network + needs the manual password; not
# run in this environment. Reading a real malicious pcap needs care — only do it
# in the throwaway lab container.
fetch-data:
	@. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh"; \
		fetch_file mta-2024-07-30 data/real-c2-exercise.pcap.zip
	@echo "Downloaded real C2 exercise zip -> data/real-c2-exercise.pcap.zip"
	@echo "Unzip it YOURSELF with the password from https://www.malware-traffic-analysis.net/about.html"
	@echo "  unzip data/real-c2-exercise.pcap.zip -d data/   (then open the .pcap in the lab container)"

up:
	docker compose up -d server lab

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

# Drop into the lab container with all network tools (tcpdump, dig, curl)
shell:
	docker compose run --rm lab bash

# Live DNS + HTTP demo + annotated capture walk-through
demo:
	docker compose run --rm demo
