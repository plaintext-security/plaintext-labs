# Lab 02 — Read Endpoint Telemetry From a Real Attack

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/02-endpoint-telemetry
make up
```

Run `make demo` to analyze a bundled `data/sysmon_events.json` — 10 events
spanning a full spear-phishing attack chain (WINWORD.EXE → cmd → PowerShell
encoded download → rundll32 LOLBin → LSASS dump → Run key persistence → C2
callback). The script reconstructs the process tree, decodes the base64
payload, and flags each technique by ATT&CK ID.

For real Sysmon telemetry, deploy [Sysmon](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon)
with the [SwiftOnSecurity config](https://github.com/SwiftOnSecurity/sysmon-config)
on your own Windows VM, export events with
`Get-WinEvent -LogName 'Microsoft-Windows-Sysmon/Operational' | ConvertTo-Json | Out-File events.json`,
then `python3 analyze.py events.json`. For public sample EVTX files, see
[EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES) +
[python-evtx](https://github.com/williballenthin/python-evtx) to export to JSON.

## Scenario
Find an attacker's footprints in real endpoint telemetry — without needing to have run the attack
yourself.

> Your own VM, or the public sample logs. (If you did Track 01, ingest your *own* attack's telemetry
> instead — same skill.)

## Do
1. [ ] Get real endpoint telemetry: load an EVTX-ATTACK-SAMPLES capture, or generate events with one
   Atomic Red Team test on your VM.
2. [ ] Find the malicious process: trace its command line and its parent. (What's a normal parent
   for this process — and is this one normal?)
3. [ ] Identify the Sysmon Event IDs that captured the activity.
4. [ ] Note what a detection for this would key on.

## Success criteria — you're done when
- [ ] You found the malicious process and its ancestry in real telemetry.
- [ ] You can name the Sysmon Event IDs involved.
- [ ] You can describe what a detection would match on.

## Deliverables
`endpoint-telemetry.md`: the malicious event, its process ancestry, the Event IDs, and your
detection idea.

## AI acceleration
Have a model explain an unfamiliar command line or Event ID — then confirm against the process tree
and the real data before calling it malicious.

## Connects forward
These events and detection ideas feed module 08 (detection-as-code) and module 11 (endpoint
hunting).

## Marketable proof
> "I deploy Sysmon and read endpoint telemetry from real attack samples — process ancestry, command
> lines, Event IDs — to find malicious activity."

## Automate & own it
**Required.** Write a script (PowerShell or Python) that pulls the relevant Event IDs from an EVTX
and flags suspicious process ancestry; AI drafts, you review it against the real sample; commit it.

## Stretch
- Run an Atomic Red Team test, capture your *own* Sysmon telemetry, and find it — closing the
  attacker→defender loop yourself.
