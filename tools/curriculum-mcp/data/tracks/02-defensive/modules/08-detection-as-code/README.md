# Module 08 — Detection-as-Code

*Module concept · [Go to the hands-on lab →](lab.md)*


**Defensive Operations** — *write the detection once, version it, test it — like software, because it is.*

## Why this matters
Detections written by hand in one SIEM's console are unversioned, untested, and trapped in that
tool. Detection-as-code treats them like software: written in a portable language (Sigma), stored
in git, tested in CI, and converted to whatever backend you run. Sigma is the community standard,
and thousands of real detections are published as Sigma rules you can read, run, and learn from.

## Objective
Write a Sigma detection for a real ATT&CK technique, convert it to your SIEM's query language, and
confirm it fires on real attack telemetry.

## The core idea
Most detections are born and die inside a single SIEM's web console: someone types a query, names
it, and moves on. No version history, no test, no review, no way to move it to another tool. It's
the same trap as a firewall rulebase edited live in the GUI for a decade — nobody can say who
changed what, why, or whether it still does what it was meant to. **Detection-as-code is just the
discipline you'd apply to any other production logic, finally applied to detections:** the rule is
a file, the file lives in git, changes go through a pull request, and CI tests the rule before it
goes live.

The piece that makes this portable is **Sigma** — a vendor-neutral YAML format for "what does this
attack look like in logs." You write the logic once against a generic log model, and a converter
(`sigma-cli` / pySigma) compiles it down to *your* backend's query language: Splunk SPL, Elastic
DSL, Sentinel KQL, whatever you run. If you've ever wished one firewall policy could push to both a
Palo Alto and a FortiGate, this is that wish granted for detections — Sigma is the intermediate
representation, and each SIEM is just a compile target. And because the SigmaHQ repo ships thousands
of peer-reviewed rules, most of the job is reading and adapting prior art, not inventing from a blank
file.

Here's the part that separates a detection engineer from someone who pastes rules: **a rule you
haven't tested against both known-bad *and* known-good is a liability, not a detection.** It is easy
to write a logically valid Sigma rule that matches the wrong field, misses an obvious variant of the
technique, or fires on every backup job at 2 a.m. The skill was never the YAML — an AI drafts that in
seconds — it's the false-positive economics: run the rule against real attack telemetry to prove it
*catches* the thing, then against a benign baseline to prove it won't *bury* the SOC. And every rule
names the ATT&CK technique it covers, because the only question leadership actually asks is "what
can't we see?" — and you can only answer that if your detections are mapped.

## Learn (~4 hrs)

**The language (~1.5 hrs)**
- [Write a Sigma rule in 120 seconds (video)](https://www.youtube.com/watch?v=h8-Mnjq6EsU) — the shape of a rule, fast; watch first, then read the spec.
- [Sigma (SigmaHQ) — project & rule repository](https://github.com/SigmaHQ/sigma) — the spec, plus thousands of real published rules to read and adapt. Skim `rules/windows/process_creation/` to see how good rules are written.

**Convert & test (~1.5 hrs)**
- [sigma-cli (SigmaHQ)](https://github.com/SigmaHQ/sigma-cli) — the converter you'll use: `sigma convert` a rule to a backend query. Read the usage section.
- [pySigma](https://github.com/SigmaHQ/pySigma) — the library underneath, for when you want conversion in a script or CI.

**Map it (~1 hr)**
- [MITRE ATT&CK](https://attack.mitre.org/) — every detection should name the technique it catches; find the technique ID for the behaviour you're detecting.
- [EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES) — real Windows attack logs to test against (the lab bundles a small slice of these).

## Key concepts
- Why detections belong in git, not a console (versioned, reviewed, tested)
- Sigma as a portable IR: write once, convert to any SIEM backend
- Rule anatomy: logsource, detection, condition
- Testing against known-bad **and** known-good — false-positive economics
- Mapping detections to ATT&CK for coverage

## AI acceleration
A model writes a Sigma rule from a description in seconds — genuinely useful. But it'll produce
logically-valid rules that match the wrong field or miss the variant; a rule you didn't test is a
liability, not a detection. The model drafts; you run it against real data, tag it, and own it.
