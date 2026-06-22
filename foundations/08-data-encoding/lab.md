# Lab 08 — Peel the Layers: Decode a Real Malware Artifact

*Variant D · misconception, predict-then-reveal. [← Back to the module concept](README.md)*

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo. The container bundles
`xxd`, `base64`, `jq`, `curl`, and `python3`, plus a `data/artifacts.txt` of real-shaped encoded
artifacts — nothing here is ever executed.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/foundations/08-data-encoding
make up      # build the container
make demo    # watch each artifact get decoded (base64 PS, hex C2, URL traversal, KEV feed)
make shell   # drop into a shell and decode them yourself
make down    # stop when done
```

CyberChef is also available in the browser at <https://gchq.github.io/CyberChef/> for visual peeling.

> **Authorization.** These are inert, decoded-not-executed samples in a local container you own. Never
> *run* a decoded malware command, and only ever fetch/test systems you own or have written permission to
> test. Defang any live URL (`hXXp`, `1.2.3[.]4`) before you write it down.

## Scenario

You're the analyst who pulled the encoded `powershell.exe -enc …` line from the module brief off a host's
event log. Your job is to peel the artifacts in `data/artifacts.txt` back to plaintext, say what each one
does, and — critically — **prove to yourself that none of it was ever secret.** The deliverable is the
short write-up a real triage analyst attaches to a ticket.

Each step runs the same rhythm: **Predict** (commit before you decode) → **Do** (peel it) → **Verdict**
(say what it is and why it was never encrypted).

## Do

1. [ ] **Warm-up — the mechanics and the tells.** Take a short string of your own and run it through two
   layers (base64, then hex) and back, both on the CLI (`echo -n … | base64`, `… | base64 -d`, `xxd -p`,
   `xxd -r -p`) and in CyberChef. **Watch the `==` appear and disappear.** Goal: you can name an encoding
   on sight from its alphabet — `==` ⇒ base64, pairs of `0`–`f` ⇒ hex, `%XX` ⇒ URL.

2. [ ] **The headline artifact — the encoded PowerShell.**
   **Predict:** is the `PS_B64` blob encryption? What do you need to read it?
   **Do:** decode it. Remember PowerShell `-enc` is UTF-16LE, so:
   `echo '<PS_B64>' | base64 -d | iconv -f utf-16le -t utf-8`. Read what it does **without running it**,
   and defang the URL.
   **Verdict:** name the technique (`iex` download cradle — ATT&CK T1059.001 + T1105) and write one
   sentence on *why base64 gave it zero secrecy.*

3. [ ] **Hex — a C2 domain in shellcode.** Decode `HEX` (`echo '<HEX>' | xxd -r -p`), then produce a hex
   *dump* of a small file (`xxd file`) and pick the readable ASCII strings out of the right-hand column.
   **Verdict:** what domain was hiding in the bytes — and note that hex is just "bytes written as text,"
   not a lock.

4. [ ] **URL-decode an attack from a log.** Decode `URLENC`
   (e.g. `python3 -c 'import urllib.parse,sys;print(urllib.parse.unquote(sys.argv[1]))' '<URLENC>'`).
   **Verdict:** name the attack the decoded path reveals, and why a filter that only checked the *raw*
   (still-encoded) request would have missed it.

5. [ ] **Peel a layered blob.** `DOUBLE` is URL-encoded *over* base64. Peel it one layer at a time,
   re-identifying the alphabet after each peel (this is the core skill). **Verdict:** what payload was at
   the bottom, and how many layers you removed.

6. [ ] **Query a real JSON feed.** Pull the live
   [CISA KEV catalog JSON](https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json)
   with `curl` and use `jq` to answer two questions — e.g. `… | jq '.vulnerabilities | length'` (how many
   CVEs?) and a per-vendor count. **Verdict:** JSON is *structure*, not secrecy — `jq` reads it because
   it was never hidden.

## Success criteria — you're done when
- [ ] You can convert a string between hex, base64, and plain text both ways, and name each encoding from its tells.
- [ ] You decoded the **real** base64 PowerShell command and can say in one sentence what it does.
- [ ] You peeled the **layered** `DOUBLE` blob to its plaintext payload, naming the alphabet at each layer.
- [ ] You decoded the hex C2 domain and the URL-encoded path-traversal and named the attack.
- [ ] You pulled two values out of the **real** KEV JSON with `jq`.
- [ ] You can explain, in your own words, **why none of this was encryption** — no key was ever needed.

## Deliverables
`encoding-notes.md` — the analyst write-up: each artifact, its decoded (defanged) value, what it does /
which attack it is, and your `jq` queries + answers against the KEV feed. End with one sentence stating
why encoding is not encryption. Commit it alongside the decode script below. Never commit live payload
URLs un-defanged, fetched second-stage files, or any malware sample.

## Automate & own it
**Required.** Write a small `decode.py` that, given an artifact, **detects its encoding from the tells**
(`==`/charset ⇒ base64, `^[0-9a-f]+$` ⇒ hex, `%` ⇒ URL) and decodes it — peeling **layered** blobs by
looping until the output is printable text. Run it over `data/artifacts.txt`. Have AI draft it; **review
every line** — especially the detection heuristics, where a wrong guess sends you down the wrong layer —
then own it. Mental model from the README: encoding changes the clothes, not the lock; your script
undresses, it never decrypts.

## AI acceleration
Hand a model the `DOUBLE` blob and ask it to identify and decode it *before* you do. It's a fast draft —
and a good adversary, because layered data is exactly where it picks the wrong peel order or calls base64
"encrypted." Catch those two errors and you've learned the module. Never run anything it decodes.

## Connects forward
"Encoding ≠ encryption" sets up **module 09 (Cryptography)** — what *actually* locks data. Hex + strings
feed forensics and malware analysis; base64/URL decoding feeds web-attack analysis; `jq` over feeds like
KEV recurs in detection and threat-intel work. Your `decode.py` becomes a tool in the **module 10 /
capstone** foundations toolkit.

## Marketable proof
> "I decode the encodings real security data actually wears — a base64 PowerShell download cradle, a hex
> C2 domain, a URL-encoded path traversal, a layered blob, a live KEV JSON feed — with `base64`, `xxd`,
> `jq`, and a script I wrote, and I never confuse encoding for encryption."

## Stretch
- Extend `decode.py` to auto-defang any URL it surfaces (`http`→`hXXp`, `.`→`[.]`) so output is safe to paste into a ticket.
- Find a multiply-encoded web-attack payload in a real public access-log dataset, decode it, and identify the attack.
