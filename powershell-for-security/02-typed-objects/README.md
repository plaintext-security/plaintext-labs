# Lab 02 — Typed Objects & the Pipeline Done Right

Environment for **Track 13 · Module 02**. The canonical instructions are the module's
[`lab.md`](https://github.com/plaintext-security/plaintext/blob/main/tracks/13-powershell-for-security/modules/02-typed-objects/lab.md).

```bash
make up      # build the pwsh 7 + PSScriptAnalyzer + Pester container
make shell   # drop into pwsh
make demo    # run the module gate (PSScriptAnalyzer + Pester) over the reference Vigil module
make down    # stop when done
```

- `Vigil/` — the **reference** module carried forward from Module 01 (`Get-VigilEvent`) now adding
  **`ConvertTo-VigilEvent`**: an advanced function (`[CmdletBinding()]`, `[OutputType([VigilEvent])]`,
  boundary validation) that normalizes raw records into typed `VigilEvent` objects. The `VigilEvent`
  class lives in `Vigil/Classes/` and is loaded into the caller's session via the manifest's
  `ScriptsToProcess`. Your job is to *write* this function against the contract, not copy it.
- `data/raw-events.json` — a small raw Windows-event export (8 records; the last is missing a required
  field on purpose, so 7 normalize; 3 are suspicious).
- `Vigil.Tests.ps1` — Pester tests: emits objects not strings, coerces fields to real types, rejects bad
  input at the boundary.
- `gate.ps1` — runs PSScriptAnalyzer + Pester and exits non-zero on failure (what CI enforces).
