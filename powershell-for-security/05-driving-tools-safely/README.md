# Lab 05 — Driving Tools & External Processes Safely

Environment for **Track 13 · Module 05**. The canonical instructions are the module's
[`lab.md`](https://github.com/plaintext-security/plaintext/blob/main/tracks/13-powershell-for-security/modules/05-driving-tools-safely/lab.md).

```bash
make up      # build the pwsh 7 + PSScriptAnalyzer + Pester container
make shell   # drop into pwsh with Vigil and the mock tool
make demo    # run the gate: AST scan (no Invoke-Expression) + PSScriptAnalyzer + Pester injection proofs
make down    # stop when done
```

> **Authorization.** This lab is offensive-capable: you feed command-injection payloads (`; rm -rf`,
> `$(...)`) to a process wrapper to prove they do **not** execute. Only run injection payloads against
> systems you own or have explicit written permission to test. Everything here runs locally in the
> container against a bundled mock tool — never point these payloads at a real or shared system.

- `Vigil/` — a **reference** cumulative module (Module 01's `Get-VigilEvent`, plus this module's
  `Invoke-VigilTool` and the `Test-VigilNoInvokeExpression` AST gate) so `make demo` proves the safe
  pattern works on a clean runner. Your job is the *process* (build the wrapper, prove the injection is
  inert, wire the gate), not copying it.
- `data/vigil-scan.sh` — a **mock external tool** that echoes each argv element it received, verbatim,
  one per line. It never eval's its input; it exists to make the argument-passing boundary *visible*.
- `data/scan-targets.json` — sample targets including **hostile filenames** (`; rm -rf`, `$(...)`,
  `&& curl`) so you can prove they arrive as one inert argument.
- `Vigil.Tests.ps1` — Pester tests that feed a malicious argument and assert the payload did **not**
  execute, and that exercise the AST gate both ways.
