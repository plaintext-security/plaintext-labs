# Lab 10 — Detecting Host Compromise

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/endpoint-hardening/10-detecting-host-compromise
make up        # stage real EVTX samples, build the container, convert to events.json
make demo      # match the example Sigma rule against the real Windows events
make shell     # drop into the container to work
make down      # stop when done
```

> Everything runs locally against real, bundled Windows attack telemetry. No SIEM required.

**Real telemetry (not an invented feed).** `make up` runs `make fetch`, which stages three genuine
Windows/Sysmon event logs from **sbousseaden/EVTX-ATTACK-SAMPLES** (a widely used, GPL-3.0 corpus of
real attack EVTX) out of the shared dataset cache — one per attack phase. `make convert` renders them
to `data/events.json` using `evtx_dump.py` (python-evtx) + `evtx_to_json.py`. You write Sigma rules
against **real Windows event data**, not a hand-authored alert blob.

## Scenario

A Windows host in the fleet has been flagged, and you have the host's Sysmon/Security event logs.
Three real attack phases are present in the telemetry (each from a separate, documented
EVTX-ATTACK-SAMPLES capture):

| Phase | What's in the events | ATT&CK |
|-------|----------------------|--------|
| Persistence | Hidden Registry Run-key value set (Sysmon EID 13) | **T1547.001** |
| Credential access | Process opening a handle to `lsass.exe` — mimikatz `sekurlsa::logonpasswords` (Sysmon EID 10) | **T1003.001** |
| Lateral movement | Remote service install (`System` EID 7045) — PsExec-style | **T1021.002 / T1543.003** |

Your job: write Sigma rules that fire on each phase, run them against the real events, and map the
coverage to ATT&CK.

## Do

1. [ ] `make demo` — watch the example rule (LSASS access, T1003.001) match against the real
   Windows events, and read `demo/show_alerts.py`'s per-phase summary. Note which event matches,
   the matching fields (`EventID`, `TargetImage`, `GrantedAccess`), and the tagged ATT&CK technique.

2. [ ] `make shell` and browse the real telemetry:
   ```bash
   jq '.[] | {phase, EventID, Channel, Image, SourceImage, TargetImage, _source}' /lab/data/events.json | less
   ```
   Identify the three attack-phase events by their `phase` tag. Note the Windows field names
   available in each (Sysmon EID 10/13 fields vs. the `System` EID 7045 service-install fields).

3. [ ] Write a Sigma rule for the **persistence** event (Registry Run-key, ATT&CK **T1547.001**).
   Save it as `rules/persistence-runkey.yml`. Logsource: `windows / sysmon`. Key fields: `EventID: 13`
   and a `TargetObject` referencing a Run key (e.g. `\\CurrentVersion\\Run`).

4. [ ] Write a Sigma rule for the **credential access** event (LSASS handle, ATT&CK **T1003.001**).
   Save it as `rules/credaccess-lsass.yml`. Key fields: `EventID: 10`, `TargetImage` containing
   `lsass.exe`. (The shipped `data/example-rule.yml` is a working reference — write your own, don't copy.)

5. [ ] Write a Sigma rule for the **lateral movement** event (remote service install, ATT&CK
   **T1021.002 / T1543.003**). Save it as `rules/lateral-service.yml`. Key fields: `EventID: 7045`
   on the `System` channel, with a `ServiceName` / `ImagePath`.

6. [ ] Test all three rules against the real events with the offline matcher:
   ```bash
   python3 detect.py --rule rules/persistence-runkey.yml --events /lab/data/events.json
   # Repeat for each rule
   ```
   Confirm each rule fires on exactly the intended phase and no others. Then convert one rule to a
   real backend with sigma-cli to prove portability: `sigma convert -t splunk rules/credaccess-lsass.yml`.

7. [ ] Map your three rules to the [ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/):
   create a layer JSON file (`coverage.json`) marking T1547.001, T1003.001, and T1021.002
   as covered (score: 1). This is your detection coverage artefact.

## Success criteria — you're done when

- [ ] Three Sigma rules, each firing on exactly the intended phase in the real `events.json`.
- [ ] No cross-firing — each rule matches only its own phase's events.
- [ ] Each rule tagged with the correct ATT&CK technique ID (T1547.001, T1003.001, T1021.002).
- [ ] A `coverage.json` ATT&CK Navigator layer marking your three techniques as covered.

## Deliverables

`rules/` directory (three `.yml` Sigma rules) + `coverage.json` (ATT&CK Navigator layer).
Commit both.

## Automate & own it

**Required.** Write a shell script `run-detections.sh` that: takes a directory of Sigma rules
and the events JSON file, runs `detect.py` against each rule, and outputs a summary table:
rule name, match count, technique ID. Exit non-zero if any rule produces zero matches (a
rule that never fires against its intended test data is broken). Have an AI draft the loop
and summary table logic; you verify the exit-code logic and test against both a matching and
a non-matching events file.

## AI acceleration

Describe a real event's Windows fields to an AI and ask it to write a Sigma rule that matches it.
Then run the rule through `detect.py` (and `sigma convert`) against the real events — does it fire?
Does it fire on the other phases too? The model drafts the rule shape; the real EVTX data tells you
if the detection logic is correct. A rule the model wrote that you never tested is a guess, not a
detection.

## Connects forward

The three Sigma rules you wrote here are the start of the organization's host detection library. The
track capstone asks you to integrate the full hardening baseline (modules 02–09) with telemetry
(module 05), compliance scanning (module 07), and detections (this module) into a single
demonstrable posture — "this host is hardened AND we know when it's being attacked."

## Marketable proof

> "I wrote ATT&CK-mapped Sigma detection rules for host-compromise indicators, tested them
> against real Windows attack telemetry (EVTX-ATTACK-SAMPLES), and produced an ATT&CK Navigator
> coverage layer showing what our endpoint detections cover and where the gaps are."

## Stretch

- Add a fourth rule for a technique you identify as a gap — pull another sample from
  EVTX-ATTACK-SAMPLES (it has ~200 across the tactics), convert it, and look for an event that
  doesn't match any of your three rules but looks suspicious. Write the rule, add the ATT&CK
  mapping, and update `coverage.json`.
- Research how Wazuh's active response feature works: a rule fires, Wazuh automatically runs
  a script (e.g. block an IP, quarantine a file). Design the active response for the lateral
  movement detection — what would you automatically block, and what is the false-positive risk?
