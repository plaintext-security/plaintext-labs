# Lab 02 — Scan and Enumerate a Target

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/offensive/02-scanning
make up      # builds the scanner + stands up the Vulhub nginx CVE-2017-7529 target (:8080)
make demo    # runs three-phase nmap scan and prints structured report
make down
```

The scan **target** is a real, named CVE: the
[Vulhub](https://github.com/vulhub/vulhub) `nginx/CVE-2017-7529`
environment — an integer overflow in the nginx range-filter module
(nginx 0.5.6–1.13.2) that leaks cache file headers and memory
(CVE-2017-7529, NVD). It is pulled on demand from the shared dataset
cache (`fetch_repo vulhub`, source name **`vulhub`**) and stood up on
host `:8080` — it is **not** committed to this repo. `make up` runs
`make target-up`, which clones Vulhub once into the cache and starts its
`nginx/CVE-2017-7529` compose.

The `lab` scanner container (nmap + Python) runs `scan.py`: three
progressive nmap phases parsed from XML into a formatted report — the
same artifact you'd hand to module 03. Version detection against the
target reveals an nginx in the CVE-2017-7529 vulnerable range; that is
the real finding the next phase acts on. (A small custom nginx victim
also ships under `victim/` for an offline reference, but the lab now
centers on the real Vulhub CVE.)

> Authorization: the Vulhub target you stand up is yours — attack it freely. The habit still matters
> everywhere else: only test systems you own or have explicit written permission to test (Vulhub, DVWA,
> PortSwigger Academy, targets you own).

## Scenario
You have a scope authorization for a single internet-facing host — an
nginx-fronted portal. Before touching vulnerability databases, run a
complete port scan and enumerate every service. Version detection will
fingerprint the nginx build; that version (and the CVE it implies) is
the input to the next phase.

## Do

1. [ ] Run `make demo` and read all three phase outputs. Which ports
   are open, what nginx **version** does `-sV` detect, and what do the
   NSE scripts reveal that `-sV` alone does not?

2. [ ] The scan targets a focused port list (22,80,443,8080,8443,3306,5432).
   Run a full-port scan from inside the container (`make shell` then
   `nmap -Pn -p- -T4 host.docker.internal`). How long does it take vs.
   the targeted scan, and does it find any additional ports?

3. [ ] The detected nginx version falls in the CVE-2017-7529 range
   (nginx ≤ 1.13.2). What is that CVE, and why is an exact version
   banner such valuable intelligence during scanning? *(Hint:
   `searchsploit nginx` and the NVD entry for CVE-2017-7529.)*

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
- [ ] Version detection identified the nginx build and you mapped it to
  the real **CVE-2017-7529** (nginx ≤ 1.13.2 range-filter integer
  overflow), confirmed against NVD.
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
`searchsploit nginx` (surfacing CVE-2017-7529) and `nuclei -t cves`
against the same target.

## Marketable proof
> "I scan and enumerate a target with Nmap — three-phase (discovery,
> version, NSE) — parse the XML output programmatically, and produce
> a structured service inventory the next phase can act on."

## Stretch
- Add a `tcpdump` service to the compose, capture the scan traffic,
  and open the PCAP in Wireshark to observe the SYN/ACK vs.
  RST pattern of open vs. closed ports.
