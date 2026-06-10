# Module 15 — PowerShell Offensive Tradecraft

*Module concept · [Go to the hands-on lab →](lab.md)*

**Offensive Security** — *the attacker's favourite tool is already installed, signed, and trusted on every Windows box.*

## Why this matters
PowerShell is the single most-abused execution vector on Windows — signed by Microsoft, present
everywhere, and able to download and run code entirely in memory. Operators reach for it constantly:
the in-memory download cradle is the canonical first move after a phish lands. Knowing this tradecraft
cold — and exactly what each move leaves in the logs — is what lets you emulate a real intrusion on an
assessment and, just as importantly, brief the defenders who have to catch it. This module is the
offensive half of a matched pair; **Defensive Module 13** is the hunt for everything you do here.

## Objective
Build and run the core PowerShell attacker primitives — encoded commands, in-memory download cradles,
and behaviour-preserving obfuscation — and explain precisely what telemetry each one generates, so you
understand both the evasion and its limits.

## The core idea
PowerShell collapses the attacker's awkward "get a file onto the box and run it" problem into a single
trusted process. The download cradle — `IEX (New-Object Net.WebClient).DownloadString(...)` — fetches a
second stage over HTTP and executes it *in memory*, so nothing lands on disk for a file-based scanner to
catch. The same logic packs into `-EncodedCommand`: a Base64 blob of UTF-16LE source that hides the
command from a shoulder-surfing analyst and from naive command-line rules. None of this is exotic; it's
the plumbing under most "fileless" intrusions, and it's why "is the binary known-bad?" stopped being a
useful question on Windows years ago.

The mental model that keeps this honest: **obfuscation is a race against the layer that has to
deobfuscate.** Base64, string-concatenation, `[char]`-code rebuilding, Invoke-Obfuscation's token tricks —
they all change the *bytes* while preserving the *behaviour*, which beats a static string signature. But
PowerShell cannot run what it hasn't reassembled, and **Script Block Logging (Event ID 4104) records the
reassembled, cleartext script block at execution time.** So obfuscation reliably defeats pre-execution
string matching and buys time against an analyst, and reliably *fails* against script-block logging and
behavioural detection. The skill is knowing which control you're actually up against.

AMSI (the Antimalware Scan Interface) is the other half of that runtime story: it hands the deobfuscated
buffer to the registered AV *just before* execution, which is why so much real tradecraft includes an AMSI
"bypass" that patches `amsiInitFailed` in memory. That, too, is loud — tampering with AMSI is itself a
high-signal detection. The through-line of the whole module: every evasion shifts you from one detection
surface to another; it never makes you invisible. The operator who understands the telemetry picks the
*quietest* path for the engagement; the one who just copies a cradle off a blog gets caught on the first
4104 event.

A word on doing this for real: PowerShell 7 on Linux (this lab) runs the language-level tradecraft
faithfully — cradles, encoding, obfuscation — but **AMSI and the Windows event channels are Windows
runtime features.** The lab teaches the mechanics deterministically and shows you the 4104 record your
command *would* generate; the lab notes the Windows-VM path for exercising AMSI itself.

## Learn (~4 hrs)

**The technique**
- [MITRE ATT&CK T1059.001 — PowerShell](https://attack.mitre.org/techniques/T1059/001/) — the canonical
  technique entry, with real procedures from named threat groups. Read the Procedure Examples to see how
  often the cradle shows up in genuine intrusions.

**Obfuscation — how, and why it's bounded**
- [Invoke-Obfuscation (Daniel Bohannon)](https://github.com/danielbohannon/Invoke-Obfuscation) — the
  reference obfuscation toolkit. Read the README and skim the `Out-*Command` modules to see the transform
  families; note it was built by a *blue-teamer* to test detection — which is exactly the lens to use.

**AMSI — the runtime gate**
- [Microsoft — How AMSI helps defend against malware](https://learn.microsoft.com/en-us/windows/win32/amsi/how-amsi-helps)
  — what AMSI is and where it hooks PowerShell, so you understand what an "AMSI bypass" is actually
  targeting (and why tampering with it is loud).

**Where it connects**
- [LOLBAS Project](https://lolbas-project.github.io/) — the living-off-the-land binaries catalogue; pair
  this module with Module 14 (LOLBins) for the non-PowerShell native-tooling angle.
- [CrowdStrike — Investigating PowerShell: Command and Script Logging](https://www.crowdstrike.com/en-us/blog/investigating-powershell-command-and-script-logging/)
  — read the *defender's* write-up of what your tradecraft leaves behind. This is the bridge straight into
  Defensive Module 13.

## Key concepts
- The in-memory download cradle (`IEX`/`DownloadString`) and why "fileless" defeats disk scanning
- `-EncodedCommand`: Base64 UTF-16LE, and how trivially it decodes
- Behaviour-preserving obfuscation (concat, `[char]`-rebuild, token tricks) vs. static signatures
- Why Script Block Logging (4104) captures the deobfuscated command regardless of obfuscation
- AMSI as the runtime scan gate, and why tampering with it is high-signal
- Every evasion trades one detection surface for another — quiet, not invisible

## AI acceleration
A model will hand you a working cradle or an obfuscated one-liner in seconds — and just as happily one
that's heavily signatured, calls a cmdlet that doesn't exist on the target, or trips AMSI on the first
line. Use it to *generate variants fast*, then verify each against the actual telemetry: run it, read the
4104 it produces, and decide whether it's quiet enough for the engagement. AI drafts the payload; you own
what it logs.
