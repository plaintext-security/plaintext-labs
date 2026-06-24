.PHONY: demo fetch-data

# Parse bundled EVTX-shaped sample + print PowerShell guide
# No Docker required — runs on macOS/Linux with Python 3
demo:
	python3 triage.py

# Download REAL .evtx samples from sbousseaden/EVTX-ATTACK-SAMPLES into data/ via
# the shared dataset cache (lib/fetch.sh) — the repo is shallow-cloned ONCE and the
# two technique samples are copied out of the cached clone.
# These are genuine Windows event logs captured from live attack techniques:
#   - encoded/obfuscated PowerShell (T1059.001, EID 4104 script-block)
#   - a remote service install for persistence (T1543.003, EID 7045)
# Provenance + exact technique paths: data/PROVENANCE.md
# NOTE (runner-validation): this hits the network AND parsing real .evtx needs a
# converter (python-evtx / evtx_dump / Get-WinEvent). Not run in this environment.
# Validate on a runner: `make fetch-data`, convert to JSON, then `python3 triage.py <json>`.
fetch-data:
	@. "$$(d=$$PWD; while [ ! -f "$$d/lib/fetch.sh" ] && [ "$$d" != / ]; do d=$$(dirname "$$d"); done; echo "$$d")/lib/fetch.sh"; \
		EVTX=$$(fetch_repo evtx-attack-samples); \
		cp "$$EVTX/Credential Access/phish_windows_credentials_powershell_scriptblockLog_4104.evtx" "data/T1059.001_encoded_powershell_4104.evtx"; \
		cp "$$EVTX/Lateral Movement/LM_Remote_Service02_7045.evtx" "data/T1543.003_service_install_7045.evtx"
	@echo "Fetched real .evtx samples -> data/ (convert to JSON to run through triage.py)"
