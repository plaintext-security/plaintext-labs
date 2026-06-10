# Lab 11 — Hunt the Endpoint

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/11-hunting-endpoint
make up      # builds the Python hunt harness
make demo    # runs hypothesis-driven hunt over bundled Sysmon events
make down
```

Bundled data: `data/sysmon_events.json` — 21 synthetic Sysmon events
from jsmith's workstation: a complete phishing-to-persistence attack
chain (Office macro → PowerShell → certutil dropper → scheduled task +
Run key) mixed with normal baseline activity. The hunt harness
`hunt.py` loads events into in-memory SQLite so you write real SQL
queries — the same skill as Velociraptor VQL or osquery, without the
infrastructure.

> **Authorization:** this lab queries bundled endpoint telemetry only —
> no live system access required.

## Scenario
The Meridian Financial threat-intel team flagged jsmith's workstation:
she downloaded an unusual `.docm` file on March 15. Form a
hypothesis, hunt the Sysmon telemetry, and confirm or refute it.

## Do

1. [ ] Run `make demo` and follow the hunt. Which ATT&CK technique is
   confirmed, and what is the evidence chain?

2. [ ] Open `hunt.py` and find Step 4 (Run key hunt). It returns two
   results — one malicious, one benign (OneDrive). Explain which field
   distinguishes them, and extend the `WHERE` clause to filter out the
   known-legitimate OneDrive path.

3. [ ] The base64 payload in Step 2 is truncated — only `$c=New-Object`
   is recovered. Add a real decoded payload to the event in
   `data/sysmon_events.json` (`iex (New-Object Net.WebClient).DownloadString(...)`)
   re-run the demo and confirm Step 2 shows the full decoded string.

4. [ ] Write a new hunt step (Step 8) that queries for *all* network
   connections (EventID 3) made by any child process of WINWORD.EXE
   (by following PID → ParentProcessId). Add it to `hunt.py` and
   run it. What IP:port appears?

5. [ ] Extend `hunt.py` with a `--sigma` flag that prints a complete
   Sigma rule (YAML) covering the Office-macro-spawns-encoded-PS
   pattern from Step 1/2.

## Success criteria — you're done when
- [ ] You can trace the full kill chain from document open to payload
  execution using only the SQL queries in `hunt.py`.
- [ ] Step 4 correctly distinguishes the malicious Run key from the
  OneDrive baseline entry.
- [ ] `--sigma` emits a valid Sigma rule that would fire on this chain.

## Deliverables
`hunt-endpoint.md`: the hypothesis, the seven-step evidence chain,
the SQL query you added for Step 8, and the Sigma rule from `--sigma`.
**This, with module 12, forms Phase 2's hunt.**

## AI acceleration
Have a model draft the `--sigma` YAML output — then validate every
field name against the [Sigma spec](https://github.com/SigmaHQ/sigma/wiki/Rule-Creation-Guide)
and test it against the actual event data. Models commonly invent
field names; the Sysmon schema is the ground truth.

## Automate & own it
**Required.** With AI drafting and you reviewing every line: refactor
`hunt.py` so each hunt step is a named function decorated with
`@step("Step N — description")`, and add a `--json` flag that emits
findings as a JSON array. Commit the refactored script.

## Connects forward
The C2 IP (185.220.101.47) and the persistence artifacts feed directly
into module 15 (threat-intel enrichment) and the Sigma rule from
Step 5 can be tested against module 09's detection-testing harness.
Network and endpoint hunts (11–12) together complete Phase 2.

## Marketable proof
> "I run hypothesis-driven endpoint hunts with SQL over Sysmon
> telemetry — process-tree pivots, LOLBin detection, and automated
> Sigma-rule generation from hunt findings."

## Stretch
- Add a parent-process-tree visualiser: given any PID, walk
  ParentProcessId links and print the ancestry chain as an indented
  tree. Run it on PID 9780 (certutil) and PID 10400 (updater.exe).
