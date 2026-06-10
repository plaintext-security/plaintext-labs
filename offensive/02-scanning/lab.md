# Lab 02 — Scan and Enumerate a Target

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/offensive/02-scanning
make up      # builds victim (nginx 1.24.0 on 80/443) + scanner container
make demo    # runs three-phase nmap scan and prints structured report
make down
```

Compose: a `victim` container (nginx 1.24.0 serving HTTP + HTTPS with a
self-signed cert naming `target.meridian-financial.com`) and a `lab`
scanner container (nmap + Python). The `scan.py` harness runs three
progressive nmap phases and parses the XML output into a formatted
report — the same artifact you'd hand to module 03.

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Scenario
Meridian's red team just received a scope authorization for
`portal.meridian-financial.com` (192.168.10.15). Before touching
vulnerability databases, run a complete port scan and enumerate every
service. Your output is the input to the next phase.

## Do

1. [ ] Run `make demo` and read all three phase outputs. Which ports
   are open, and what do the NSE scripts reveal that `-sV` alone does
   not?

2. [ ] The current scan only targets ports 22,80,443,8080,8443,3306,5432.
   Run a full-port scan from inside the container (`make shell` then
   `nmap -Pn -p- -T4 target`). How long does it take vs. the targeted
   scan, and does it find any additional ports?

3. [ ] The victim's TLS certificate reveals its CN. What hostname does
   it disclose, and why is that useful intelligence during recon?

4. [ ] The scan uses TCP connect (`-sT` equivalent — no SYN because no
   root needed). Explain: what's the difference between a SYN scan
   (`-sS`) and a connect scan (`-sT`)? Which leaves more traces in the
   target's logs? *(Hint: look at what a SYN scan's "half-open
   handshake" means.)*

5. [ ] Extend `scan.py` with a `--json` flag that writes the scan
   results to `scan-notes.json` — a structured array of
   `{port, service, version}` objects suitable as input to module 03's
   vulnerability lookup. Commit it.

## Success criteria — you're done when
- [ ] You can explain the three-phase scan methodology (discovery →
  version → NSE) and why each phase exists.
- [ ] You understand why the docker compose needs `cap_add: [NET_RAW]`
  for SYN scans, and what breaks without it.
- [ ] `scan.py --json` emits valid JSON you could pipe to `jq`.

## Deliverables
`scan-notes.md`: the open ports, service/version for each, and one
NSE result explained. Optionally: `scan-notes.json` (from `--json`).

## AI acceleration
Paste a confusing NSE script output or nmap XML snippet to a model
for a plain-English explanation — then verify against the
[nmap NSE docs](https://nmap.org/nsedoc/). NSE output formats vary
by script; the docs are the authority.

## Automate & own it
**Required.** With AI drafting and you reviewing every line: add
`--json` to `scan.py` so it also writes `scan-notes.json`. This is
the feed from this phase into module 03's vulnerability lookup.

## Connects forward
The `{service, version}` pairs from `scan-notes.json` are the direct
input to module 03 (vulnerability identification) — you'll run
`searchsploit nginx 1.24.0` and `nuclei -t cves` against the same
target.

## Marketable proof
> "I scan and enumerate a target with Nmap — three-phase (discovery,
> version, NSE) — parse the XML output programmatically, and produce
> a structured service inventory the next phase can act on."

## Stretch
- Add a `tcpdump` service to the compose, capture the scan traffic,
  and open the PCAP in Wireshark to observe the SYN/ACK vs.
  RST pattern of open vs. closed ports.
