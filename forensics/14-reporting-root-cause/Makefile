.PHONY: demo lint fetch-data

# Optional REAL artifact so the report's findings/IOCs can be cross-checked against a
# genuine log from the anchor case's escalation step — Zerologon (CVE-2020-1472), used
# by Lunar Spider for lateral movement. Public EVTX-ATTACK-SAMPLES corpus. See
# PROVENANCE.md. The writing exercise needs no download; this is additive.
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
	@echo "  Reporting & Root-Cause Analysis Lab"
	@echo "============================================================"
	@echo ""
	@echo "Files for this exercise:"
	@echo "  data/report-template.md   — fill in this template"
	@echo "  data/incident-findings.md — raw investigation findings"
	@echo "  scripts/lint_report.py    — structural linter"
	@echo ""
	@echo "--- GRADING RUBRIC ---"
	@echo ""
	@echo "Executive Summary (25 pts)"
	@echo "  [ ] Under 250 words"
	@echo "  [ ] No jargon — a CFO can understand it completely"
	@echo "  [ ] Scope paragraph distinguishes confirmed vs. exposed"
	@echo "  [ ] Exactly 3 remediation priorities listed"
	@echo ""
	@echo "Technical Findings (30 pts)"
	@echo "  [ ] At least 6 findings"
	@echo "  [ ] Each finding has an artifact citation ([Artifact] → [Field] = [Value])"
	@echo "  [ ] Each finding has an ATT&CK technique ID"
	@echo "  [ ] No overstatement — confirmed findings only"
	@echo ""
	@echo "Root-Cause Analysis (25 pts)"
	@echo "  [ ] 5 Whys applied with at least 4 levels"
	@echo "  [ ] Root cause is a control gap, not a human behaviour"
	@echo "  [ ] Root cause statement uses the prescribed format"
	@echo ""
	@echo "IOC Table (10 pts)"
	@echo "  [ ] At least 5 IOCs with all columns populated"
	@echo "  [ ] Includes IP, Domain, File Hash, File Path, and IAM entries"
	@echo ""
	@echo "Lint Check (10 pts)"
	@echo "  [ ] python3 scripts/lint_report.py <report.md> exits 0"
	@echo ""
	@echo "To check your report:"
	@echo "  python3 scripts/lint_report.py your-report.md"
	@echo "  python3 scripts/lint_report.py your-report.md --strict"
	@echo "============================================================"

lint:
	@if [ -z "$(REPORT)" ]; then \
		echo "Usage: make lint REPORT=your-report.md"; \
		exit 1; \
	fi
	python3 scripts/lint_report.py $(REPORT)
