# Module 08 — Data & Encoding

*Module concept · [Go to the hands-on lab →](lab.md)*


**Foundations** — *security data is a mess of formats; reading them is a daily skill.*

## Why this matters
Indicators, payloads, tokens, and captured data show up base64'd, hex-encoded, URL-encoded,
or buried in JSON. Forensics and malware analysis live in hex; web attacks live in URL and
base64 encoding; everything emits JSON. Confusing *encoding* (reversible, not secret) with
*encryption* is a classic beginner mistake this module kills early.

## Objective
Recognise and convert between common encodings (hex, base64, URL), read JSON, and query it on
the command line.

## The core idea
Security data shows up disguised — base64'd, hex-dumped, URL-encoded, nested in JSON — and the single
most important idea here kills a classic beginner error: **encoding is not encryption.** Encoding
(base64, hex, URL/percent) is a *reversible reshaping for transport*; it provides exactly zero secrecy,
because anyone can decode it without a key. Encryption needs a key. Mistaking "it's base64, so it's
hidden" for security is a real, common, dangerous confusion — you *will* find secrets "protected" by
nothing but base64 in the wild. Internalise that line now and a lot of later analysis gets clearer.

The practical skill is fast recognition and conversion: spot base64 vs. hex vs. URL-encoding on sight,
read a hex dump (forensics and malware analysis live here), and query JSON with `jq` (everything emits
JSON). Real data is often *layered* — a payload base64'd inside URL-encoding inside JSON — so the move
is peeling one layer at a time, which is exactly what CyberChef lets you *see* transformation by
transformation.

The judgment: models identify and decode a blob instantly ("what is this?"), which is genuinely handy —
but verify by decoding it yourself, because a model that guesses the wrong layer or mis-identifies the
encoding sends you down a wrong path with confidence. The tool is fast; the confirmation is yours.

## Learn (~2 hrs)

**Encodings & character sets**
- [Joel Spolsky — The Absolute Minimum Every Developer Must Know About Unicode & Character Sets](https://www.joelonsoftware.com/2003/10/08/the-absolute-minimum-every-software-developer-absolutely-positively-must-know-about-unicode-and-character-sets-no-excuses/) — the classic that makes encoding click: encoding ≠ encryption.
- [CyberChef](https://gchq.github.io/CyberChef/) — "the cyber swiss-army knife"; build a recipe to peel apart layered base64/hex/URL and *see* each transformation.

**Querying structured data**
- [jq manual](https://jqlang.org/manual/) — slice and filter JSON from the command line; you'll use this constantly.

## Key concepts
- Encoding ≠ encryption (reversible, not secret)
- Hex and ASCII; reading a hex dump
- Base64 and base64url
- URL / percent encoding
- JSON structure and querying it with `jq`

## AI acceleration
Models decode and identify encodings instantly — paste a blob and ask "what is this?" Useful,
but verify by decoding it yourself in CyberChef; a model guessing the wrong layer sends you
down a wrong path.
