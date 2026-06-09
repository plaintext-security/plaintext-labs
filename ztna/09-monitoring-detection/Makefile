# Module 09 — Monitoring & Detection in Zero Trust lab.
# Standard targets: up / down / reset / demo / shell / convert / detect
.PHONY: up down reset demo shell convert detect

up:        ## Build and start the lab container
	docker compose up -d --build

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the lab container
	docker compose exec lab bash

# ── Worked example (the "what good looks like" demo) ─────────────────────────
demo:      ## Run the unexpected-country detection against the bundled ZT access logs
	docker compose run --rm lab sh -c '\
		echo "=== Zero Trust Detection Lab ==="; \
		echo ""; \
		echo "Log summary: 20 structured ZT access events (Meridian Financial)"; \
		echo "Signals planted: unexpected-country login, auth flood, data exfil volume"; \
		echo ""; \
		echo "== 1. Fire the unexpected-country Sigma rule =="; \
		echo "   Rule: examples/zt-unexpected-country.yml"; \
		echo "   Logs: data/access-logs.jsonl"; \
		echo ""; \
		python detect.py examples/zt-unexpected-country.yml data/access-logs.jsonl; \
		echo ""; \
		echo "== 2. What would this look like in Splunk? =="; \
		echo "   (sigma-cli converts the same rule to a SIEM query)"; \
		echo "   Note: the ZT logsource does not have a standard Sigma pipeline."; \
		echo "   Below converts to a generic keyword query as a reference:"; \
		sigma convert -t splunk examples/zt-unexpected-country.yml || \
		  echo "   (conversion requires a matching pipeline — see the lab notes)"; \
		echo ""; \
		echo "== Detection summary =="; \
		echo "   In a perimeter model these events are invisible (traffic never hit a firewall)."; \
		echo "   In ZT, every access is logged — the signal is richer, not noisier."; \
		echo "   Unexpected country on an authenticated session = high fidelity. Correlate with HR travel data to cut FPs."'

# ── Your turn: point these at the rule you write ─────────────────────────────
convert:   ## make convert RULE=your-rule.yml — convert your rule to SPL
	docker compose run --rm lab sigma convert -t splunk -p sysmon $(RULE)

detect:    ## make detect RULE=your-rule.yml — run your rule against the ZT access logs
	docker compose run --rm lab python detect.py $(RULE) data/access-logs.jsonl
