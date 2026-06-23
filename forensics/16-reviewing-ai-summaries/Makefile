# Forensics Module 16 — Reviewing AI Incident Summaries.
# Standard targets every reference lab provides: up / down / reset / shell / demo.
.PHONY: up down reset shell demo verify

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
