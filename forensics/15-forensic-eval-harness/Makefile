# Forensics Module 15 — Forensic Eval Harness.
# Standard targets every reference lab provides: up / down / reset / shell / demo.
.PHONY: up down reset shell demo detect eval fetch-data

# Optional REAL labelled samples to harden the held-out corpus beyond the inert
# fixtures (see PROVENANCE.md). Two sources, both verified, both deferred:
#   - a real Latrodectus PE from MalwareBazaar (abuse.ch) — a true-malicious item
#     to score the YARA rule against (zip stays packed; password 'infected').
#   - a real Windows .evtx from EVTX-ATTACK-SAMPLES — a genuine artifact behind a
#     timestomp/behaviour near-miss.
# The committed inert fixtures remain the zero-cost default; fetch-data is additive.
MB_API   := https://mb-api.abuse.ch/api/v1/
EVTX_URL := https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Defense%20Evasion/DE_1102_security_log_cleared.evtx

up:        ## Build and start the lab container
	docker compose up -d --build
	@echo "Container ready. Run 'make demo' for the scorecard + regression gate."

down:      ## Stop and remove the container
	docker compose down

reset:     ## Tear down completely (container + local image + volumes)
	docker compose down --rmi local --volumes --remove-orphans

shell:     ## Open a shell in the lab container
	docker compose exec lab bash

# --- Worked example: the scorecard, then the gate going green then RED ---------
demo:      ## Score the GOOD detectors (gate green), then the REGRESSED ones (gate red)
	docker compose run --rm lab python3 /scripts/eval.py --demo

# --- Your turn -----------------------------------------------------------------
detect:    ## Run the detectors over the corpus → per-file verdicts (data/verdicts.json)
	docker compose run --rm lab python3 /scripts/eval.py --detect

eval:      ## Print the confusion matrix + precision/recall/F1/FP-rate scorecard
	docker compose run --rm lab python3 /scripts/eval.py --score

# --- Optional: pull REAL labelled samples to expand the corpus -----------------
# Requires a free abuse.ch Auth-Key for the MalwareBazaar half:
#   make fetch-data MB_AUTHKEY=... MB_SHA256=<a real Latrodectus sample hash>
# The malware zip is downloaded but NEVER unzipped here (it is live malware; the
# password is 'infected' — unpack only in an isolated analysis VM you own). The
# .evtx is a benign-to-handle real event log. Label any fetched item yourself in
# data/labels.json before scoring — never let a tool self-label the ground truth.
fetch-data:  ## Download real labelled samples (MalwareBazaar PE + EVTX) — see PROVENANCE.md
	@mkdir -p data/real-samples
	@if [ -f data/real-samples/DE_1102_security_log_cleared.evtx ]; then \
		echo "exists: data/real-samples/DE_1102_security_log_cleared.evtx"; \
	else \
		echo "fetch:  data/real-samples/DE_1102_security_log_cleared.evtx"; \
		curl -fsSL "$(EVTX_URL)" -o data/real-samples/DE_1102_security_log_cleared.evtx; \
	fi
	@if [ -n "$(MB_AUTHKEY)" ] && [ -n "$(MB_SHA256)" ]; then \
		echo "fetch:  data/real-samples/$(MB_SHA256).zip (packed, NOT unzipped)"; \
		curl -fsSL --header "Auth-Key: $(MB_AUTHKEY)" \
			--data "query=get_file&sha256_hash=$(MB_SHA256)" \
			"$(MB_API)" -o "data/real-samples/$(MB_SHA256).zip"; \
	else \
		echo "skip:   MalwareBazaar PE (set MB_AUTHKEY and MB_SHA256 to fetch a real Latrodectus sample)"; \
	fi
	@echo "Done. Record SHA-256s in PROVENANCE.md and label new items in data/labels.json before scoring."
