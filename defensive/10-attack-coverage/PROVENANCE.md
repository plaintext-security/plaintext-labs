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

## One-line citation

> MITRE ATT&CK (https://attack.mitre.org/) and ATT&CK Navigator
> (https://github.com/mitre-attack/attack-navigator). Layer generated from the lab's
> Sigma rule set by `coverage.py`.
