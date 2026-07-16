.PHONY: up down reset shell demo gen-zeek gen-sysmon

up:
	docker compose up -d --build

# Regenerate data/zeek/*.log from the SAME anchor PCAP as data/eve.json (second
# sensor for the cross-source stretch). Runs on the HOST (needs Docker; the lab
# container has Python, not Zeek). See data/PROVENANCE.md.
gen-zeek:
	./gen_zeek.sh

# Fetch the Sysmon EVTX (third sensor — endpoint telemetry). GPL upstream, so
# fetched + checksum-verified, never committed (*.evtx is gitignored). Parse with
# python-evtx. See data/PROVENANCE.md.
gen-sysmon:
	./gen_sysmon.sh

down:
	docker compose down

reset:
	docker compose down --rmi local --volumes --remove-orphans

shell:
	docker compose exec lab bash

# Reference demo: the shell=True wrapper EXECUTES an injected command; the
# shell=False + validated wrapper refuses the same payload. Injection, then fix.
demo:
	docker compose run --rm lab python demo.py
