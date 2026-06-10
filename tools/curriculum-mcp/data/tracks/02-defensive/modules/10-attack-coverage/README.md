# Module 10 — ATT&CK Mapping & Coverage

*Module concept · [Go to the hands-on lab →](lab.md)*


**Defensive Operations** — *you can't defend what you can't measure; map your detections to know your gaps.*

## Why this matters
A pile of detections isn't a strategy. Mapping every detection to MITRE ATT&CK turns "we have 200
rules" into "we cover these techniques and we're blind to those" — which is how you prioritise what to
build next and communicate posture to leadership. The ATT&CK Navigator makes coverage (and gaps)
visual; it's a standard SOC artifact.

## Objective
Map your detections to MITRE ATT&CK, visualise coverage and gaps in the Navigator, and prioritise what
to build next.

## The core idea
A pile of detections isn't a strategy — it's inventory. **MITRE ATT&CK** is the shared map that turns
"we have 200 rules" into "we cover *these* techniques and we're blind to *those*." The mental model:
ATT&CK is a coordinate system for attacker behaviour — tactics are the goal (*why*: persistence,
exfiltration), techniques are the method (*how*), sub-techniques the specific variant. Plot each
detection and data source onto that grid with the Navigator and your coverage — and your gaps —
become *visible*, which is how you prioritise what to build next and how you state posture to
leadership in language they can act on.

The trap, and why this module has teeth: coverage maps are seductive because they're trivial to
inflate. A green Navigator is **not** the same as being defended. A detection mapped to T1059 that
only catches one variant — or that doesn't actually fire (module 09) — still shows green. So
**coverage ≠ effectiveness**, and "do we have a rule" is not "would we catch it." The honest version
weights by *threat relevance* — what actually targets you (intel, module 15) — rather than raw
technique count; total coverage of techniques nobody uses against you is wasted effort dressed up as
progress.

The judgment: a model speeds mapping and drafting Navigator layers, but it will confidently map a
rule to the wrong technique or overstate what a detection really catches — and an inflated coverage
map is *worse* than none, because it manufactures false confidence. Verify every mapping against what
the detection actually matches.

## Learn (~4 hrs)

**The framework & tooling**
- [MITRE ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/) — build coverage layers on the ATT&CK matrix; the standard visualisation.
- [MITRE ATT&CK — Resources / Getting Started](https://attack.mitre.org/resources/) — tactics, techniques, and how to use them for coverage.

**Coverage method**
- [DeTT&CT (Detect Tactics, Techniques & Combat Threats)](https://github.com/rabobank-cdc/DeTTECT) — an OSS method/tool for scoring detection and data-source coverage against ATT&CK.

## Key concepts
- Tactics vs techniques vs sub-techniques
- Mapping detections and data sources to ATT&CK
- Visualising coverage and gaps (Navigator layers)
- Prioritising by threat relevance (what targets *you*)
- Coverage ≠ effectiveness (a mapped detection still has to work)

## AI acceleration
A model speeds mapping detections to techniques and drafting a Navigator layer — but it'll confidently
map a rule to the wrong technique or overstate coverage. Verify each mapping against what the detection
actually matches; an inflated coverage map is worse than none.
