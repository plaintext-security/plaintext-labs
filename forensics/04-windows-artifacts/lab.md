# Lab 04 — Windows Artifacts

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — its environment lives in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/forensics/04-windows-artifacts
make up        # build the chainsaw + python-registry container
make demo      # parse the bundled EVTX and registry hive; print key findings
make shell     # drop in to explore interactively
make down      # stop when done
```

The container includes `chainsaw` and `python-registry`. Seed files:
- `data/security.evtx` — a small Windows Security event log with planted attack events
- `data/ntuser.dat` — a small synthetic registry hive with persistence and MRU entries

> Everything runs locally against bundled data. No authorization needed.

## Scenario
The Meridian IR team has triaged the suspect workstation and collected two key artifacts from the compromised finance host: a Security event log and the user's registry hive. The endpoint was running for approximately 12 hours after the anomalous outbound connection before the IR team arrived. Your task is to parse both artifacts and answer three questions: **Who authenticated?** **What ran?** **How did it persist?**

> Only examine evidence you are authorised to handle. In a real case, these files would arrive with a verified hash from Module 01.

## Do

1. [ ] **Hunt the event log with chainsaw.**
   Run `chainsaw hunt` against `data/security.evtx` with Sigma rules:
   ```bash
   chainsaw hunt data/security.evtx --sigma /opt/sigma-rules/ --mapping /opt/chainsaw/mappings/sigma-event-logs-all.yml
   ```
   If Sigma rules are unavailable, use `chainsaw search` to find logon events:
   ```bash
   chainsaw search --event-id 4624 data/security.evtx
   chainsaw search --event-id 4688 data/security.evtx
   ```
   Document: which accounts authenticated? Which processes were created? Note any 4688 events with suspicious parent-child relationships (e.g., `cmd.exe` spawned by `outlook.exe`).

2. [ ] **Find the log clear event.**
   Search for Event ID 1102 (Security log cleared):
   ```bash
   chainsaw search --event-id 1102 data/security.evtx
   ```
   Was the log cleared? If so, who cleared it and when? What does this tell you about the attacker's post-exploitation behavior?

3. [ ] **Parse the registry hive for persistence.**
   Use `python-registry` to enumerate the run keys in `data/ntuser.dat`:
   ```python
   from Registry import Registry
   reg = Registry.Registry('data/ntuser.dat')
   key = reg.open('Software\\Microsoft\\Windows\\CurrentVersion\\Run')
   for value in key.values():
       print(f"{value.name()} = {value.value()}")
   ```
   What autorun entries are present? Are any suspicious (unexpected paths, encoded commands, or unknown executables)?

4. [ ] **Extract MRU (Most Recently Used) entries.**
   Look for recently opened files and typed paths in the hive:
   ```python
   # RecentDocs MRU
   key = reg.open('Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RecentDocs')
   # TypedPaths MRU (Explorer address bar)
   key = reg.open('Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\TypedPaths')
   ```
   What files were recently opened? Do the paths align with the exfiltration scenario from Module 01?

5. [ ] **Document your findings.**
   Write `windows-artifact-findings.md` with:
   - Table of authentication events (Event ID 4624): account name, logon type, source IP, timestamp
   - Table of process creation events (Event ID 4688): process name, parent process, command line, timestamp
   - List of autorun persistence entries from the registry
   - MRU entries that are relevant to the investigation
   - Short paragraph: attacker timeline reconstruction based on log + registry evidence combined

## Success criteria — you're done when
- [ ] At least three Event ID 4624 or 4688 events are documented with fields extracted.
- [ ] Persistence entries from the registry are identified and noted as suspicious or benign.
- [ ] MRU entries are extracted and correlated with the Meridian scenario.
- [ ] `windows-artifact-findings.md` includes a timeline narrative.
- [ ] You can explain what Event ID 1102 means and why finding it is significant.

## Deliverables
Commit `windows-artifact-findings.md` to your fork. Do not commit any modified versions of the seed EVTX or hive files.

## Automate & own it
**Required.** Write a Python script `parse-windows-artifacts.py` that:
1. Takes paths to an EVTX file and a registry hive as arguments.
2. Extracts all 4624, 4625, and 4688 events from the EVTX using `python-evtx` or `chainsaw`'s JSON output.
3. Extracts all run key values from the hive.
4. Produces a Markdown report with a timeline section and a persistence section.

Have a model draft the script; **read every line** and run it against the seed data before committing. This is the automation move for Windows triage — a first-pass report that tells you within 60 seconds what a machine was doing and what persisted.

## AI acceleration
Feed chainsaw's JSON output to a model and ask it to identify the three most suspicious events and explain why. For the registry, describe the value you found and ask whether it's a known persistence technique. Cross-check every ATT&CK technique ID the model names against [attack.mitre.org](https://attack.mitre.org) before including them in your report — models confuse technique IDs.

## Connects forward
The execution and authentication events you surface here feed directly into the super-timeline in Module 07 (plaso ingests EVTX and the timeline correlates events across sources). The persistence mechanisms you identify connect to Module 08 (triage and live response — detecting persistence at scale) and Module 12 (malware artifacts in IR).

## Marketable proof
> "I parse Windows event logs and registry hives offline using chainsaw and python-registry — surfacing authentication anomalies, execution chains, and persistence mechanisms from raw forensic artifacts."

## Stretch
- Install `MFTECmd` (Eric Zimmerman) in the container and parse the `$MFT` from a test image — compare the execution timestamps to what you see in the EVTX.
- Research Amcache: write a Python snippet using `python-registry` to enumerate `Amcache.hve`'s `InventoryApplicationFile` entries and extract SHA-1 hashes of executed files.
