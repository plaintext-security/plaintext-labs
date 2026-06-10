# Lab 12 — Hunt for C2 Beaconing

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/12-hunting-network
make up      # builds the Python scoring harness
make demo    # runs RITA-style beacon hunt over bundled Zeek conn.log
make down
```

Bundled data: `data/zeek/conn.log` — 22 synthetic connections from the Meridian
Financial estate: 10 C2 callbacks, update-service heartbeats, CDN browsing, and a
large exfil. The beacon scorer `beacon_hunt.py` re-implements RITA's three-component
model (interval CV, byte consistency, connection count) without requiring the full RITA
+ MongoDB stack.

> **Authorization:** this lab analyzes bundled log data only — no live network.

## Scenario
The Meridian SOC received a tip: an insider may have exfiltrated data last weekend.
You have Zeek `conn.log` from the corporate perimeter for that window. Hunt for
command-and-control beaconing to find the implant responsible for staging the exfil.

## Do

1. [ ] Run `make demo` and read the ranked beacon candidates. Which (src, dst, port)
   session scores highest, and why?

2. [ ] Understand the three score components: interval CV, byte-size consistency,
   connection count. Adjust the weights in `beacon_hunt.py` — does the C2 host
   (185.220.101.47) rise or fall relative to the update service (204.79.197.200)?

3. [ ] The top-scoring session is a legitimate update service. Explain in one sentence
   why it scores higher than the actual C2 in this dataset. *(Hint: what effect does
   the large exfil connection have on the C2 session's interval CV?)*

4. [ ] Add a DNS-based C2 detection step: scan `conn.log` for connections to the same
   external IP on multiple ports and flag any dest with ≥ 3 unique destination ports.

5. [ ] Extend `beacon_hunt.py` with a `--min-score` flag; default 30. Emit findings as
   JSON suitable for piping to a SIEM.

## Success criteria — you're done when
- [ ] You can explain why the update service outscored the C2 beacon, with reference to
  CV math.
- [ ] You correctly identified 185.220.101.47 as the exfil-staging C2 despite its
  lower beacon score, using multi-indicator analysis.
- [ ] `beacon_hunt.py` accepts `--min-score` and emits JSON output.

## Deliverables
`hunt-network.md`: beacon candidate table, CV analysis for the two top sessions, your
verdict on 185.220.101.47, and the JSON snippet from your extended script. **This, with
module 11, forms Phase 2's hunt.**

## AI acceleration
Have a model generate the JSON output extension — then verify every field name and
value against the actual `conn.log` data. Models hallucinate field names; the data is
the ground truth.

## Automate & own it
**Required.** With AI drafting and you reviewing every line: add a second output mode
to `beacon_hunt.py` that writes a Markdown threat-hunting report to
`hunt-network.md`. It should include the session table, score breakdown, and a verdict
paragraph. Commit the extended script and the generated report.

## Connects forward
The C2 IP you surfaced (185.220.101.47) feeds directly into module 15 (threat intel
enrichment) — you'll look it up in ThreatFox to confirm attribution. Network and
endpoint hunts (11–12) together complete Phase 2.

## Marketable proof
> "I hunt for C2 beaconing with a RITA-style scorer I built and understand — interval
> jitter analysis, multi-indicator triage, and automated JSON reporting."

## Stretch
- Add a DGA score: compute bigram entropy for each resolved hostname in `dns.log`
  (create a minimal synthetic `dns.log` with 5 DGA-style domains) and flag those with
  entropy > 3.5 bits/char.
