# Provenance — Module 10, ATT&CK Mapping & Coverage

## This lab is already grounded in real artifacts

Unlike a synthetic-dataset lab, the substance here is **real by construction**: every
technique ID is a genuine MITRE ATT&CK technique (cited by `Txxxx[.xxx]`), and the
output is a real, schema-valid **ATT&CK Navigator layer** you upload to the actual
hosted Navigator to visualise. There is no synthetic dataset to swap out — the fix
for this lab was only to drop the fictional org name, not to wire a new source.

## The real schema / source

- **MITRE ATT&CK** — the technique catalogue the priority list and rule tags refer to
  (e.g. T1059.001, T1547.001, T1003.001, T1021.001, T1486, T1566.001):
  https://attack.mitre.org/
- **ATT&CK Navigator** — the tool that renders `navigator_layer.json`, and the
  defining source of the layer JSON schema this lab emits (`versions.layer`, the
  `techniques[]` array of `{techniqueID, score, color, comment}`, the `gradient`):
  - App (verified): https://mitre-attack.github.io/attack-navigator/
  - Source + layer-format docs:
    https://github.com/mitre-attack/attack-navigator
    (layer schema under `nav-app/src/assets/` / `layers/` in that repo)
- **STIX / raw ATT&CK data**, if you want to generate priority lists programmatically
  rather than hand-curating `priority_techniques.txt`:
  https://github.com/mitre-attack/attack-stix-data

`coverage.py` writes a layer at `versions: {layer: 4.5, navigator: 4.9.1, attack: 14}`
— a real, current Navigator layer revision the hosted app accepts.

## What ships in this repo

`navigator_layer.json` is the **generated** output of `make demo` (re-emitted by
`coverage.py` from the rule tags); it is committed so the lab has a worked example to
upload. `priority_techniques.txt` is a curated must-cover list using neutral naming
("the SOC"). The `rules/` are the same Sigma rules used in modules 08–09, mapped to
their ATT&CK tags.

## Closing the loop with real tests (not hand-waved coverage)

"Covered" is only honest if you can *demonstrate* the rule fires on the technique.
Every ID in `priority_techniques.txt` is a real MITRE ATT&CK technique that has a
real **Atomic Red Team** test — the atomic that exercises it — so a green cell is
verifiable, not asserted:

- Atomic Red Team (MIT), registered as `atomic-red-team` in `lib/sources.tsv`:
  https://github.com/redcanaryco/atomic-red-team
- Per-technique tests at `atomics/<ID>/` — e.g.
  [`atomics/T1059.001`](https://github.com/redcanaryco/atomic-red-team/tree/master/atomics/T1059.001),
  `T1547.001`, `T1003.001`, `T1021.001`, `T1486`, `T1566.001` (all six priorities
  have a published atomic).

The coverage map says *which* techniques your rules claim; the atomics are how you
**prove** each claim (run the atomic on a host you own → confirm the rule fires in
your SIEM). Module 09 wires that purple-team loop, including an offline
`make fetch-events` that scores the shipped rules over real EVTX-ATTACK-SAMPLES
telemetry. Coverage (this lab) + validation (module 09) is the full picture.

## One-line citation

> MITRE ATT&CK (https://attack.mitre.org/) and ATT&CK Navigator
> (https://github.com/mitre-attack/attack-navigator). Layer generated from the lab's
> Sigma rule set by `coverage.py`.
