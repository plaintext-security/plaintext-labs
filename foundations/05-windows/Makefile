.PHONY: demo fetch-data

# Parse bundled EVTX-shaped sample + print PowerShell guide
# No Docker required — runs on macOS/Linux with Python 3
demo:
	python3 triage.py

# Download REAL .evtx samples from sbousseaden/EVTX-ATTACK-SAMPLES into data/.
# These are genuine Windows event logs captured from live attack techniques:
#   - encoded/obfuscated PowerShell (T1059.001, EID 4104 script-block)
#   - a remote service install for persistence (T1543.003, EID 7045)
# Provenance + exact technique paths: data/PROVENANCE.md
# NOTE (runner-validation): this hits the network AND parsing real .evtx needs a
# converter (python-evtx / evtx_dump / Get-WinEvent). Not run in this environment.
# Validate on a runner: `make fetch-data`, convert to JSON, then `python3 triage.py <json>`.
fetch-data:
	curl -fsSL -o "data/T1059.001_encoded_powershell_4104.evtx" \
		"https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Credential%20Access/phish_windows_credentials_powershell_scriptblockLog_4104.evtx"
	curl -fsSL -o "data/T1543.003_service_install_7045.evtx" \
		"https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Lateral%20Movement/LM_Remote_Service02_7045.evtx"
	@echo "Fetched real .evtx samples -> data/ (convert to JSON to run through triage.py)"
