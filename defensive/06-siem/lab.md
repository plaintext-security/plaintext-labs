# Lab 06 — Catch an Attack in a SIEM

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/06-siem
make up      # builds the Python SIEM harness
make demo    # ingests multi-source events, runs 6 correlation rules, prints alerts
make down
```

Bundled data: `data/events.json` — 18 normalized events from four
sources (Sysmon, Zeek, Suricata, sshd) covering two simultaneous
incidents: an Office-macro phishing compromise on WS-JSMITH and an
SSH brute-force success on SRV-01. The `siem.py` harness implements
the four core SIEM operations — ingest/normalize, correlate, alert,
query — using SQLite so you write real SQL rules without a
multi-GB Elasticsearch cluster.

> **Authorization:** this lab analyzes bundled log data only — no
> live network or host access.

## Scenario
The Meridian SOC has one pane: a terminal. Ingest the morning's
multi-source telemetry, run your correlation rules, and triage the
resulting alerts by severity before stand-up.

## Do

1. [ ] Run `make demo`. Read the alert output: how many alerts fired,
   and from which sources did the evidence come? Can you trace the
   CRITICAL alert's evidence chain through the event store?

2. [ ] Open `siem.py`. The `rule_run_key` function hard-filters
   OneDrive and Microsoft from the Run key results. Why is that
   necessary, and what risk does it introduce? Add a comment.

3. [ ] Add a new correlation rule using the `@rule(...)` decorator:
   *Suspicious process in ProgramData* — fires on EventID 1 where
   `process` contains `ProgramData`. Does it fire on the demo data?
   How many false positives would you expect in production?

4. [ ] Extend `siem.py` with a `--export-rules` flag that prints each
   rule's title, severity, and technique as a JSON array. This is the
   start of *detection-as-code* — rules committed alongside the harness.

5. [ ] Add a `count` field to each alert and update the dashboard to
   show total alert volume, not just distinct rule count. Which rule
   fires most often on this dataset?

## Success criteria — you're done when
- [ ] You can explain why `rule_ssh_brute_success` is CRITICAL while
  `rule_ssh_brute` is only MEDIUM — what's the additional evidence?
- [ ] Your new ProgramData rule fires on the demo data with the
  correct host and timestamp.
- [ ] `--export-rules` emits valid JSON.

## Deliverables
`siem.md`: the six-alert triage table (severity, rule, host, detail),
the answer to the OneDrive-filter question, and the new ProgramData
rule code. **This lab is the correlation layer that ties modules
04–05 and 08–12 together.**

## AI acceleration
Have a model draft the `@rule` function body for your new rule — then
test it against the event store yourself. A rule that fires on the
attack but not the baseline is the goal; models can't verify that for
you.

## Automate & own it
**Required.** With AI drafting and you reviewing every line: move the
rule definitions out of `siem.py` and into `rules/` as individual
Python modules, auto-discovered by `siem.py` at startup using
`importlib`. Commit the refactored harness so new rules can be added
without touching `siem.py`.

## Connects forward
Every other module in this track feeds the SIEM: Sigma rules (08)
become correlation rules here, hunting (11–12) produces hypotheses to
operationalize, and SOAR (15) triggers off these alerts. Threat-intel
(14) enriches the IPs that appear in the alert details.

## Marketable proof
> "I build and tune multi-source SIEM correlation rules — across
> endpoint, network, and IDS telemetry — and triage the alert queue
> to a prioritized, evidence-backed recommendation."

## Stretch
- Wire in the module 04 `zeek/conn.log` and module 05 `eve.json` as
  additional event sources — extend `normalize()` to parse them and
  confirm the existing rules still fire with the richer dataset.
