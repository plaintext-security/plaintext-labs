# Module 03 — Vulnerability Identification

*Module concept · [Go to the hands-on lab →](lab.md)*


**Offensive Security** — *from "this host runs X 1.2.3" to "here's the known way in, and how urgent it is."*

## Why this matters
A service version is only interesting if you know its weaknesses. This module connects
enumeration to the real vulnerability ecosystem — CVEs, CWEs, exploit databases, and
(crucially) which vulnerabilities are *actually being exploited in the wild*. Anyone can
paste a version into a search box; the skill is judging real exploitability and urgency, not
just collecting CVSS scores.

## Objective
Map a service/version to its known vulnerabilities, and assess real-world exploitability and
urgency using authoritative sources.

## The core idea
A service version is trivia until you connect it to its weaknesses — and the real skill isn't *finding*
CVEs (a search box does that), it's judging which ones actually matter. Get the vocabulary straight,
because people blur it constantly: a **CVE** is a specific named vulnerability; a **CWE** is the
weakness *type* behind it (CVE-2021-44228 is an instance of CWE-502); **CVSS** scores how bad it is
*if* exploited. The classic mistake is treating CVSS as a to-do list, worst-first — a 9.8 that nobody
exploits is less urgent than a 7.5 that's in every breach report this month.

That gap is exactly what **KEV** and **EPSS** close. CISA's Known Exploited Vulnerabilities catalog is
"confirmed exploited in the wild — this is real, fix it"; EPSS estimates the *probability* something
will be exploited. Together they turn a wall of CVSS numbers into actual prioritisation. This is the
same triage a defender does in vulnerability management — the other side of this exact coin — so
learning to read NVD/KEV/EPSS makes you bilingual: you can tell a defender not just "you run CVE-X"
but "it's in KEV, here's the urgency."

The judgment: a public PoC on Exploit-DB is a *lead*, not a guarantee — it may target a different
build, be deliberately defanged, or be malware aimed at lazy attackers. Read it before you run it. And
models are dangerously fluent here: they will state a wrong affected-version range or invent a
plausible-looking CVE ID with complete confidence. In vulnerability work a hallucinated "fact" costs
you hours or sends you down a dead end — confirm against NVD/KEV directly, every time.

## Learn (~3 hrs)

**The vulnerability ecosystem**
- [NIST National Vulnerability Database (NVD)](https://nvd.nist.gov/) — search a product/version for its CVEs; the canonical record, with CVSS scoring.
- [MITRE CWE](https://cwe.mitre.org/) — the weakness *type* a CVE maps back to (e.g. CWE-89, SQL injection).

**What actually matters**
- [CISA Known Exploited Vulnerabilities (KEV) catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) — vulnerabilities confirmed exploited in the wild; your real-world prioritisation signal.
- [Exploit-DB](https://www.exploit-db.com/) — public proof-of-concept exploits mapped to CVEs (and the backend for `searchsploit`).

## Key concepts
- CVE, CWE, and CVSS — what each is and isn't
- Mapping a service/version to known CVEs
- KEV and EPSS: exploited-in-the-wild and exploitation-likelihood signals
- Finding and judging public proof-of-concept exploits
- Prioritising by real risk, not raw CVSS

## AI acceleration
Models summarise a CVE and its impact well — and will also confidently state a wrong version
range or invent a CVE ID. Always confirm against NVD/KEV directly; in vulnerability work a
hallucinated "fact" wastes hours or sends you down a dead end.
