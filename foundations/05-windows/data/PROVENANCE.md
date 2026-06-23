# Data provenance — 05-windows event-log samples

## Real .evtx samples (`make fetch-data`)

The genuine artifacts for this lab come from **sbousseaden/EVTX-ATTACK-SAMPLES** — a curated
collection of **real Windows event logs captured while executing specific MITRE ATT&CK techniques**,
the same repo cited in the module README.

- **Source repo:** <https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES>
- **Samples fetched into `data/` by `make fetch-data`:**

  1. **Encoded / obfuscated PowerShell — T1059.001** (the lab's "decode the `-EncodedCommand`" lesson)
     - Path: `Credential Access/phish_windows_credentials_powershell_scriptblockLog_4104.evtx`
     - Raw: <https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Credential%20Access/phish_windows_credentials_powershell_scriptblockLog_4104.evtx>
     - A real PowerShell **script-block log (Event ID 4104)** from a phishing-driven credential-grab —
       the cleartext PowerShell that the encoded `-enc` blob on the command line was hiding.

  2. **Service-install persistence — T1543.003** (the lab's "find the persistence" lesson)
     - Path: `Lateral Movement/LM_Remote_Service02_7045.evtx`
     - Raw: <https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES/raw/master/Lateral%20Movement/LM_Remote_Service02_7045.evtx>
     - A real **System Event ID 7045** "a new service was installed" record — the same
       persistence signal modeled in `evtx_sample.json`.

  Both URLs were verified to return HTTP 200 binary `.evtx` files.

## Why the bundled `evtx_sample.json` still exists

`triage.py` reads JSON, not raw `.evtx`. The committed `evtx_sample.json` is an **EVTX-shaped JSON
model** of a commodity-loader intrusion (encoded PowerShell 4688 + 7045 service install + Run-key
4657), so the lab runs offline with zero dependencies. It is now scrubbed of fictional naming
(domain `CORP`, a generic `WinTelemetryUpdater` masquerading service). It is a teaching model, not a
real capture — the real captures are the `.evtx` files above.

## RUNNER-VALIDATION NEEDED

Two things are deferred to a runner:
1. `make fetch-data` reaches the network (GitHub) — not run here.
2. Feeding the real `.evtx` through `triage.py` requires converting it to the tool's JSON shape with
   a parser — e.g. `evtx_dump` / Python `python-evtx`, or `Get-WinEvent -Path sample.evtx | ConvertTo-Json`
   on Windows. Validate the convert→`python3 triage.py <json>` path on a runner with that tooling.
