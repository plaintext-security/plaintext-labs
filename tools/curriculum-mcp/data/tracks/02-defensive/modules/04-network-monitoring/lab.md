# Lab 04 — Find Malware on the Wire with Zeek

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/04-network-monitoring
make up
```

Run `make demo` to analyze a bundled set of synthetic Zeek logs
(`data/zeek/conn.log`, `dns.log`, `http.log`) that model a real C2
compromise — beaconing at ~300 s intervals, DGA queries, a PowerShell
dropper download, and 8 MB of outbound exfil.

For the full real-traffic exercise: download a malicious capture from
[Malware-Traffic-Analysis.net](https://www.malware-traffic-analysis.net/)
(each post has a PCAP + write-up), drop it in this directory, and run:

```bash
# generates conn.log, dns.log, http.log etc. in this directory
PCAP=your-capture.pcap make zeek
python3 analyze.py .   # analyze the generated logs
```

## Scenario
Run Zeek over a real malicious PCAP and find the attack in its logs — fully self-contained, no prior
track required.

> Analyse only the public training PCAP (or your own captures).

## Do
1. [ ] Run Zeek over the PCAP to generate its logs (conn, dns, http, ssl, files).
2. [ ] Find the suspicious activity: unusual DNS, a C2 connection, or a downloaded file. (Where would
   beaconing show up?)
3. [ ] Extract the indicators (IPs, domains, hashes) — then check your findings against the site's
   write-up.
4. [ ] Note a detection you could build from the network artifact.

## Success criteria — you're done when
- [ ] Zeek logs are generated and you found the malicious activity in them.
- [ ] You extracted indicators and they match the published write-up.
- [ ] You can describe a network detection for the behaviour.

## Deliverables
`nsm.md`: the Zeek logs that mattered, the indicators you pulled, and your detection idea.

## AI acceleration
Have a model summarise a large Zeek log or explain a DNS pattern — then verify against the write-up.
The model triages; the ground truth is the log plus the analyst's report.

## Connects forward
These network indicators and detections feed module 05 (IDS), module 08 (detection-as-code), and
module 12 (network hunting).

## Marketable proof
> "I run Zeek over real malicious traffic and pull C2/exfil indicators from its logs — network
> visibility that catches what endpoints miss."

## Automate & own it
**Required.** Script a pass over the Zeek logs that flags the indicators (suspicious DNS, long
connections, rare destinations); AI drafts, you validate against the known-bad PCAP; commit it.

## Stretch
- Feed the Zeek logs into your Elastic pipeline (module 01) and build a dashboard.
