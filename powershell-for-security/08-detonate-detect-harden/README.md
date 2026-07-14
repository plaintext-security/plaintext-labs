# Lab 08 — PowerShell as the Weapon: Detonate, Detect, Harden

Environment for **Track 13 · Module 08**. The canonical instructions are the module's
[`lab.md`](https://github.com/plaintext-security/plaintext/blob/main/tracks/13-powershell-for-security/modules/08-detonate-detect-harden/lab.md).

```bash
make up         # build the pwsh 7 + PSScriptAnalyzer + Pester container
make detonate   # benign detonation: encode a -EncodedCommand, decode + run a BENIGN payload, capture telemetry
make demo       # detonate -> capture telemetry -> gate: detection fires on malicious, quiet on benign held-out
make shell      # drop into pwsh
make down       # stop when done
```

**Authorization.** Only test systems you own or have explicit written permission to test.
The detonation here is **benign** (writes a marker file, prints a beacon string — no network
calls, no persistence, no destructive actions) and targets the **shipped lab only**.

- `data/Invoke-BenignDetonation.ps1` — reproduces the *shape* of an encoded/obfuscated abuse
  (base64 `-EncodedCommand` + an obfuscated scriptblock) with a harmless payload, and emits the
  telemetry (EID 4104 script-block logging + EID 4688 process creation) the detection consumes.
- `data/telemetry-malicious.json` — a committed malicious-pattern telemetry sample (5 events:
  an `-EncodedCommand` cradle, an `IEX` download cradle, format-operator + char-code obfuscation,
  and a `-nop -w hidden -exec bypass` launch).
- `data/telemetry-benign.json` — the **held-out benign** sample (legit admin/SOC PowerShell) the
  detection must stay **quiet** on.
- `Vigil/` — the **reference** cumulative module (`Get-VigilEvent`, `Invoke-VigilEnrichment`, and
  the new `New-VigilDetection`) so `make demo` proves the detection works on a clean runner.

### What runs here, and what does NOT

The **detonation** (base64 encode/decode, running an obfuscated-but-benign scriptblock) and the
**detection over captured telemetry** run cross-platform on `pwsh` 7 in this Linux container.

Live **AMSI** and **Constrained Language Mode enforcement** are **Windows-only** and are **NOT**
demonstrated here — they are taught in the module and `lab.md` as *assessed-not-demonstrated* /
an optional Windows-VM step. This container does not enforce AMSI or CLM; do not read the green
gate as proof that those Windows controls are active.
