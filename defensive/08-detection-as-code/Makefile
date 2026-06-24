# Module 08 — Detection-as-Code lab.
# Standard targets every reference lab provides: up / down / reset / demo.
.PHONY: up down reset demo shell convert detect fetch-data

up:        ## Build and start the lab container
	docker compose up -d --build

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the lab container
	docker compose exec lab bash

# --- Worked example (the "what good looks like" demo) ---------------------
demo:      ## Convert the example rule to SPL, then fire it at the sample telemetry
	docker compose run --rm lab sh -c '\
		echo "== 1. Convert the Sigma rule to Splunk SPL =="; \
		sigma convert -t splunk -p sysmon examples/encoded_powershell.yml; \
		echo; \
		echo "== 2. Fire the same rule at the sample telemetry =="; \
		python detect.py examples/encoded_powershell.yml data/events.jsonl'

# --- Your turn: point these at the rule you write -------------------------
convert:   ## make convert RULE=detection.yml — convert your rule to SPL
	docker compose run --rm lab sigma convert -t splunk -p sysmon $(RULE)

detect:    ## make detect RULE=detection.yml — run your rule against the sample data
	docker compose run --rm lab python detect.py $(RULE) data/events.jsonl

# --- Real attacker-tooling event (deferred; not run in CI) ----------------
# Pull a genuine encoded-PowerShell test from Atomic Red Team T1059.001 and convert
# it into the events.jsonl shape detect.py consumes. See data/PROVENANCE.md.
ART_T1059_001_URL ?= https://raw.githubusercontent.com/redcanaryco/atomic-red-team/master/atomics/T1059.001/T1059.001.yaml
fetch-data: ## Download the real ART T1059.001 atomics and convert → data/real_events.jsonl
	@mkdir -p data/raw
	@echo "Downloading $(ART_T1059_001_URL) ..."
	curl -fL -o data/raw/T1059.001.yaml "$(ART_T1059_001_URL)"
	docker compose run --rm lab python convert_atomic.py data/raw/T1059.001.yaml data/real_events.jsonl
	@echo "Done. Real encoded-PowerShell event(s) in data/real_events.jsonl."
	@echo "Fire your rule at them:  make detect RULE=detection.yml  (point detect.py at data/real_events.jsonl)"

