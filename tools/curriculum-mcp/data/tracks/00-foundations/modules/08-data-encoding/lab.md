# Lab 08 — Decode the Layers (Real Artifacts)

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/foundations/08-data-encoding
make up     # build container with xxd, jq, curl, python3
make demo   # decode base64 PS command, hex C2 domain, URL traversal, KEV feed
make shell  # interactive shell to try the encoding commands yourself
```

CyberChef is also available in the browser at https://gchq.github.io/CyberChef/ for visual exploration.

## Scenario
Decode the kinds of encoded artifacts you'll actually meet — a base64 PowerShell command and
a live threat-intel feed — not toy strings.

## Do
1. [ ] **Warm-up (mechanics):** encode a short string through two layers (base64, then hex)
   and decode it back — by hand on the CLI and again in CyberChef — so the transformations
   are clear.
2. [ ] **Decode a real artifact:** take a real base64-encoded PowerShell command — the kind
   found in actual intrusions (grab one from a public sandbox report or a
   [Malware-Traffic-Analysis.net](https://www.malware-traffic-analysis.net/) write-up) — and
   decode it **without executing it**. What was it trying to do?
3. [ ] **Hex:** produce and read a hex dump of a small file and pick out the ASCII strings.
4. [ ] **Query real JSON:** pull the live
   [CISA KEV catalog JSON](https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json)
   and use `jq` to query it — e.g. count the CVEs, or list those from one vendor. (Same data
   you met in module 01.)

## Success criteria — you're done when
- [ ] You can convert a string between hex, base64, and plain text both ways.
- [ ] You decoded a **real** base64 PowerShell command and can say what it does.
- [ ] You pulled a value out of the **real** KEV JSON feed with `jq`.
- [ ] You can explain why none of this is encryption.

## Deliverables
`encoding-notes.md`: the decoded (defanged) PowerShell and what it does, plus the `jq`
queries you ran against the KEV feed and their answers.

## AI acceleration
Have a model identify an unknown encoding or decode the PowerShell — then confirm by decoding
it yourself, and note when it guessed the wrong layer order. Never run the decoded command.

## Connects forward
Hex and strings feed Track 04 (malware) and Track 03 (forensics); base64/URL encoding feed
Track 01 (web attacks); `jq` over feeds like KEV feeds Track 02 and Track 09.

## Marketable proof
> "I decode the encodings real security data shows up in — a base64 PowerShell stager, a hex
> dump, a live threat-intel JSON feed — with CyberChef and jq, without confusing encoding for
> encryption."

## Automate & own it
**Required.** Write a script that pulls the live CISA KEV feed and answers your `jq` questions
programmatically (AI-drafted, you review the logic); commit it.

## Stretch
- Decode a multiply-encoded real web-attack payload (URL- then base64-encoded) from a public
  web-server log or dataset, and identify the attack.
