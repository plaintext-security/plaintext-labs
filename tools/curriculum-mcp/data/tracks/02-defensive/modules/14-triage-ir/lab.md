# Lab 14 — Run an Incident in TheHive

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/14-triage-ir
make up      # builds the Python triage harness
make demo    # walks through INC-2024-0315-001 across all 5 NIST phases
make down
```

Bundled data: `data/incident_pack.json` — a structured incident pack
for INC-2024-0315-001 (the Meridian Cobalt Strike compromise from
modules 02/05/06/11/14): initial alert, 8 observables, 8-event
timeline, threat-intel enrichment, affected assets, and per-phase
triage questions. The `triage.py` harness walks through NIST SP
800-61 phases (Detection → Containment → Eradication → Recovery →
Post-Incident Review) so you practice the reasoning without needing a
TheHive/Jira instance.

> **Authorization:** this lab analyzes a bundled simulated incident
> only — no live system access.

## Scenario
You're on call when the IDS fires. The alert shows `ET POLICY PE EXE
or DLL Windows file download HTTP` from 10.0.1.55. Run `make demo` to
open the case, work through the triage questions, and reach a verdict.

## Do

1. [ ] Run `make demo` and follow all five phases. At the triage
   checklist (Phase 1), write your answers before reading the threat-
   intel enrichment section — then compare. Did the observable data
   alone support a CRITICAL verdict?

2. [ ] The containment phase lists four "Do NOT" actions. Pick any
   two and explain the forensic or operational risk they introduce.
   Add your explanation as a comment in `triage.py`.

3. [ ] The eradication phase lists 4 persistence artifacts. The
   harness shows `stage1.exe` in the timeline but it's not in the
   eradication list. Is that a gap? Update `incident_pack.json` to
   add it (or add a comment explaining why it's omitted).

4. [ ] The post-incident review ranks 4 improvement actions. Add a
   fifth: a detection rule for certutil being used as a downloader.
   Write it as a Sigma rule YAML snippet in `incident.md`.

5. [ ] Extend `triage.py` with a `--generate-report` flag that writes
   `incident.md` — a Markdown incident report template populated with
   the pack's incident ID, timeline, observables table, and five
   blank answer sections. Commit it.

## Success criteria — you're done when
- [ ] You answered all Phase 1 triage questions before reading the
  threat-intel section and reached the correct severity.
- [ ] Your Sigma rule for certutil downloading is syntactically valid.
- [ ] `--generate-report` produces a `incident.md` template.

## Deliverables
`incident.md`: the triage decision and rationale, the containment
actions you'd take, the eradication checklist (with stage1.exe
addressed), your certutil Sigma rule, and the one improvement action
you'd prioritize. **This is the Phase 2 capstone incident report.**

## AI acceleration
Have a model draft the Sigma rule for certutil LOLBin download — then
test it against the Sysmon event data from module 11. Models commonly
confuse `CommandLine|contains` with `CommandLine|startswith`; the
[Sigma spec](https://github.com/SigmaHQ/sigma/wiki/Rule-Creation-Guide)
is the authority.

## Automate & own it
**Required.** With AI drafting and you reviewing every line: add a
`--api` flag to `triage.py` that outputs the incident pack to TheHive
v5's API format (JSON with `title`, `severity`, `tags`, `observables`
arrays per the [TheHive schema](https://docs.strangebee.com/thehive/api-docs/#tag/Case/operation/Create%20case)).
Commit the extended script.

## Connects forward
The C2 indicator (185.220.101.47) connects to module 15's
threat-intel enrichment — this is where the ThreatFox lookup you built
pays off. The improvement actions from the post-incident review connect
to module 16 (SOAR automation) and back to module 08 (detection-as-code).

## Marketable proof
> "I triage real alerts through the NIST SP 800-61 lifecycle — from
> initial IDS signal to a documented root-cause verdict — and turn each
> incident into a concrete detection improvement."

## Stretch
- Build a `--score` flag that assigns a numeric risk score (1–100)
  to the incident based on: C2 in threat intel (×2), encoded PS
  (×1.5), persistence count (×1 per artifact), affected segment
  sensitivity (FINANCE = ×2, DMZ = ×1). Apply it to INC-2024-0315-001
  and justify the weighting in `incident.md`.
