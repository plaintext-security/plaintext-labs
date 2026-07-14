# Lab 01 — Modern PowerShell Toolchain & Module Skeleton

Environment for **Track 13 · Module 01**. The canonical instructions are the module's
[`lab.md`](https://github.com/plaintext-security/plaintext/blob/main/tracks/13-powershell-for-security/modules/01-modern-toolchain/lab.md).

```bash
make up      # build the pwsh 7 + PSScriptAnalyzer + Pester container
make shell   # drop into pwsh
make demo    # run the module gate (PSScriptAnalyzer + Pester) over the reference Vigil module
make down    # stop when done
```

- `legacy/hunt.ps1` — the loose script **you migrate** (intentionally dirty; do not rewrite it, wrap it).
- `Vigil/` — a **reference** end-state module (manifest + `Get-VigilEvent`) so `make demo` proves the
  toolchain works on a clean runner. Your job is the *process* (spec → migrate → gate → ADR), not copying it.
- `data/sample.json` — a small Windows-event export (7 events; 3 suspicious).
