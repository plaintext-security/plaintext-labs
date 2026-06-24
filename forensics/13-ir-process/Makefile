.PHONY: demo fetch-data

# Optional REAL artifact so the (synthetic) brief can be grounded against a genuine
# log from the anchor case's escalation technique — Zerologon (CVE-2020-1472), which
# Lunar Spider used for lateral movement. Public EVTX-ATTACK-SAMPLES corpus. See
# PROVENANCE.md. The exercise itself needs no download; this is additive.
EVTX_URL := https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Credential%20Access/Zerologon_CVE-2020-1472_DFIR_System_NetLogon_Error_EventID_5805.evtx

fetch-data:  ## Download a real Zerologon .evtx into data/artifacts/ (idempotent) — see PROVENANCE.md
	@mkdir -p data/artifacts
	@if [ -f data/artifacts/Zerologon_CVE-2020-1472_DFIR_System_NetLogon_Error_EventID_5805.evtx ]; then \
		echo "exists: data/artifacts/Zerologon_CVE-2020-1472_..._5805.evtx"; \
	else \
		echo "fetch:  data/artifacts/Zerologon_CVE-2020-1472_..._5805.evtx"; \
		curl -fsSL "$(EVTX_URL)" -o "data/artifacts/Zerologon_CVE-2020-1472_DFIR_System_NetLogon_Error_EventID_5805.evtx"; \
	fi
	@echo "Done. Verify SHA-256 against PROVENANCE.md."

demo:
	@echo "============================================================"
	@echo "  Incident Response Process Exercise (NIST SP 800-61)"
	@echo "============================================================"
	@echo ""
	@echo "Incident Brief: data/incident-brief.md"
	@echo "Timeline CSV:   data/incident-timeline.csv"
	@echo ""
	@cat data/incident-brief.md
	@echo ""
	@echo "============================================================"
	@echo "  EXERCISE PROMPTS"
	@echo "  1. Identify all four NIST SP 800-61 phases in the brief."
	@echo "  2. Fill the three [UNKNOWN] gaps with NIST-cited recommendations."
	@echo "  3. Evaluate the 4hr 16min containment delay."
	@echo "  4. Identify the eradication gap (cloud artifacts)."
	@echo "  5. Write lessons learned answering: earliest detection point,"
	@echo "     and highest-value single control improvement."
	@echo "  6. Complete the NIST phase scorecard."
	@echo "============================================================"
	@echo ""
	@echo "Deliverable: ir-analysis.md committed to your portfolio repo."
