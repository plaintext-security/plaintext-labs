# Forensics Module 16 — Reviewing AI Incident Summaries.
# Standard targets every reference lab provides: up / down / reset / shell / demo.
.PHONY: up down reset shell demo verify fetch-data

# Optional REAL artifact to verify AI claims against (see PROVENANCE.md). The
# committed artifacts (auth.log, winlog_4688.csv, cloudtrail.json, pe_features.json)
# are the zero-cost default; this adds a genuine Windows .evtx so a learner can
# practise tracing an AI-asserted CVE/technique to a real event log. The anchored
# Lunar Spider case used Zerologon (CVE-2020-1472), so a real Zerologon log is the
# on-theme choice from the public EVTX-ATTACK-SAMPLES corpus, pulled from the shared
# dataset cache (lib/fetch.sh, source name evtx-attack-samples).

up:        ## Build and start the lab container
	docker compose up -d --build
	@echo "Container ready. Run 'make demo' for the claim-verifier walkthrough."

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image + volumes)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the lab container
	docker compose exec lab bash

# --- Worked example: cross-reference every claim to a bundled artifact --------
# The verifier exits 1 when it finds unsupported claims (the expected outcome for
# this seeded summary — finding fabrications IS the demo passing). It exits 2 on a
# fail-loud error (unreadable input / unparseable summary), which is a real failure.
# So: treat exit 1 as demo-success, anything else as demo-failure.
demo:      ## Run the claim-verifier over the seeded summary; flag unsupported claims
	docker compose run --rm lab python3 /scripts/check_summary.py \
		/data/ai-incident-summary.md /data/artifacts; \
	rc=$$?; \
	if [ $$rc -eq 1 ]; then \
		echo; echo "demo OK: verifier flagged the planted fabrications (exit 1 expected)"; \
		exit 0; \
	else \
		echo; echo "demo FAILED: expected exit 1 (fabrications flagged), got $$rc"; \
		exit 1; \
	fi

# --- Your turn: point it at your own summary / artifact set -------------------
verify:    ## make verify SUMMARY=... ARTIFACTS=... — run the verifier on your inputs
	docker compose run --rm lab python3 /scripts/check_summary.py $(SUMMARY) $(ARTIFACTS)

# --- Optional: pull a REAL .evtx to verify a claim against a genuine log -------
fetch-data:  ## Download a real Zerologon .evtx into data/artifacts/ (idempotent) — see PROVENANCE.md
	@mkdir -p data/artifacts
	@if [ -f data/artifacts/Zerologon_CVE-2020-1472_DFIR_System_NetLogon_Error_EventID_5805.evtx ]; then \
		echo "exists: data/artifacts/Zerologon_CVE-2020-1472_..._5805.evtx"; \
	else \
		echo "fetch:  data/artifacts/Zerologon_CVE-2020-1472_..._5805.evtx"; \
		. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh"; \
		repo=$$(fetch_repo evtx-attack-samples); \
		cp "$$repo/Credential Access/Zerologon_CVE-2020-1472_DFIR_System_NetLogon_Error_EventID_5805.evtx" "data/artifacts/Zerologon_CVE-2020-1472_DFIR_System_NetLogon_Error_EventID_5805.evtx"; \
	fi
	@echo "Done. Verify SHA-256 against PROVENANCE.md. Use it to practise tracing an AI-asserted CVE to a real log."
