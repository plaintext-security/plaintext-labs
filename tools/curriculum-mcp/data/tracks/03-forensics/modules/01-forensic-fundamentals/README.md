# Module 01 — Forensic Fundamentals & Evidence Handling

*Module concept · [Go to the hands-on lab →](lab.md)*


**Digital Forensics & IR** — *every conclusion you ever draw in this track stands or falls on what you do in the first five minutes.*

## Why this matters
Forensic work is downstream of trust: a timeline reconstruction, a root-cause verdict, a legal hold — all of it is only as reliable as the chain of custody that precedes it. Get the fundamentals wrong and every artifact you surface later is tainted. Courts have excluded forensic evidence because the examiner couldn't prove the image matched the original; IR reports have been challenged because the hash wasn't taken before first access. This module is the foundation everything else is built on, and it pays forward to every subsequent module in the track.

## Objective
Explain why forensic integrity matters, compute and verify hashes with `sha256sum` and `dc3dd`, document a chain of custody for collected evidence, and articulate the difference between a forensic image and a live snapshot.

## The core idea
The foundational move in digital forensics is the same one accountants call "closing the books": you fix a moment in time, prove that your record of it is accurate, and then never touch the original again. In practice that means **hashing before you work**. A cryptographic hash (SHA-256 is the minimum today; MD5 alone is no longer sufficient) is a fingerprint for a file or disk. If the hash you take at collection matches the hash you recompute before analysis, nothing changed in between — not your hand, not a bad cable, not a malware dropper that woke up mid-collection. If the hashes diverge, you have a broken chain and your findings are uncorroborated.

**Chain of custody** is the paper trail that proves who had possession of the evidence and when. In a court context that means a physical form (or its digital equivalent) that travels with the evidence: received from, transferred to, stored at, each signed and timestamped. In an enterprise IR context it means the same thing in your ticketing system or evidence management tool — an audit trail that shows no unauthorized hand touched the evidence. The chain isn't bureaucracy; it is the mechanism by which anyone — including an adversary's attorney — can verify that you didn't plant, alter, or misinterpret what you found.

**Forensic imaging** is the discipline of capturing evidence *before* analysis, not during. You never analyze the original — you work on a verified copy of a verified image. This matters most for storage media: a forensic duplicate is a sector-by-sector copy that includes deleted space, slack space, and unallocated areas, not just the files the OS presents. Tools like `dc3dd` (a forensic-purpose fork of GNU `dd`) compute and log the hash *during* the imaging pass, which proves the image was accurate at the moment of capture — not "I hashed it later and it happened to match." The hash happens inline, not as an afterthought.

The practical corollary is **write-blocking**: you must prevent any write to the source media before or during acquisition. Hardware write blockers are the gold standard; software alternatives (Linux's `blockdev --setro`) exist but require discipline. Mounting evidence media without a write block — even read-only — can update access timestamps, modify journal entries, and alter metadata you needed to preserve. The cardinal sin is mounting the original without a blocker, running an antivirus scan "to check," and then trying to explain to opposing counsel why dozens of metadata fields changed.

Finally, understand the difference between **volatile and non-volatile evidence**, because volatility determines collection order. RAM is volatile — it disappears the moment the machine loses power, and it contains process state, decrypted keys, running network connections, and injected code that never touches disk. Disk artifacts are non-volatile. The forensic principle is: collect in order of volatility, highest first. That said, a live system's volatile state is also a *live system* — active network connections, running malware, processes modifying disk. The decision of whether to pull the power (dead-box acquisition) or work live is one of the first judgment calls you'll make in a real IR, and there is no universally right answer.

## Learn (~3 hrs)

**Foundations (~1 hr)**
- [NIST SP 800-86: Guide to Integrating Forensic Techniques into Incident Response](https://csrc.nist.gov/pubs/sp/800/86/final) — the authoritative U.S. government framework; read sections 2–3 for evidence handling and collection principles. Free PDF, no login.
- [RFC 3227 — Guidelines for Evidence Collection and Archiving](https://www.rfc-editor.org/rfc/rfc3227) — two pages of distilled guidance on collection order and handling; short enough to read twice.

**Hashing and imaging (~1 hr)**
- [dc3dd man page and usage guide (DCFL)](https://sourceforge.net/projects/dc3dd/files/dc3dd/7.2/) — the forensic `dd`; skim the flag listing (`hash`, `log`, `hof`) to understand what it gives you that plain `dd` doesn't.

**Chain of custody (~1 hr)**
- [FBI — Digital Evidence Collection & Handling Guide](https://www.fbi.gov/services/information-management) — federal standard for evidence chain of custody and documentation. See Law Enforcement guidance sections.
- [RFC 3227 — Guidelines for Evidence Collection and Archiving (also above)](https://www.rfc-editor.org/rfc/rfc3227) — includes explicit chain-of-custody requirements, handling procedures, and template forms.

## Key concepts
- A cryptographic hash is a tamper-evident seal; SHA-256 is the current minimum.
- `dc3dd` computes the hash *inline* during imaging, which is stronger than hashing after.
- Chain of custody proves who had possession, when, and that nothing changed between hands.
- Forensic imaging captures unallocated space and deleted data — it is not a file copy.
- Write-blocking is mandatory before any contact with source media.
- Collect in order of volatility: RAM → running processes → disk → offline storage.
- Dead-box vs. live acquisition is a judgment call driven by the investigation's needs, not habit.

## AI acceleration
AI is most useful here as a chain-of-custody drafter and report scaffolder: describe what you collected and when, and a model will produce a formatted evidence log you then verify and sign. Where AI is *not* useful: computing hashes (trust the tool, not the model), and deciding whether to pull power (that judgment is yours, not a model's). Use AI to draft; never use it to substitute for running the actual hash command and comparing the output yourself.
