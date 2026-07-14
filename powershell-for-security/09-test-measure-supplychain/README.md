# Lab 09 — Test, Measure & Supply-Chain Gate

Environment for **Track 13 · Module 09**. The canonical instructions are the module's
[`lab.md`](https://github.com/plaintext-security/plaintext/blob/main/tracks/13-powershell-for-security/modules/09-test-measure-supplychain/lab.md).

```bash
make up      # build the pwsh 7 + PSScriptAnalyzer 1.22.0 + Pester 5.6.1 container
make shell   # drop into pwsh
make eval    # run just the detection eval (held-out scorecard + regression gate)
make demo    # run the FULL gate: analyzer + Pester (coverage) + eval + sign/verify
make down    # stop when done
```

## What's here

- `Vigil/` — the cumulative reference module. Carries the prior cmdlets (`Get-VigilEvent`,
  `Invoke-VigilEnrichment`) and adds **`Get-VigilDetection`**, the binary classifier the eval scores.
- `data/tuning/` — the labelled samples you MAY inspect while building the detection.
- `data/heldout/` — the labelled samples the eval scores **only** — never tuned against. Scoring on the
  tuning set is a memory test, not a measurement.
- `eval.ps1` — runs `Get-VigilDetection` over the held-out corpus, prints a **precision/recall/FP-rate
  scorecard**, and **exits non-zero on a regression** (recall below a floor or FP-rate above a ceiling).
- `Vigil.Tests.ps1` — real `Pester` v5 tests: a `Should -Invoke` **mock** of the feed edge and
  **unhappy-path** assertions, not a replay of the demo.
- `sign.ps1` — the supply-chain signing loop: mint a self-signed code-signing cert (openssl, since
  `New-SelfSignedCertificate` is Windows-only), `Set-AuthenticodeSignature` the module, verify the block,
  and prove **tampering is caught**.
- `gate.ps1` — the full CI gate: analyzer + Pester (with a coverage floor) + eval + sign/verify.
- `PSScriptAnalyzerSettings.psd1` — the lint settings the gate enforces.

## Prove the regression gate bites

```bash
make shell
# Remove a detection token, e.g. delete 'FromBase64String' from Get-VigilDetection's -Token default,
# then:
pwsh -NoProfile -File ./eval.ps1     # recall drops below the floor -> non-zero exit (build fails)
# Restore the token, re-run -> passes.
```

## Honesty note (assessed-not-demonstrated on Linux)

`Set-AuthenticodeSignature` writes a signature block on Linux/pwsh, and `sign.ps1` proves the full loop —
sign → verify-before-trust → reject-on-tamper — deterministically and offline. **Full Authenticode chain
trust** (`Get-AuthenticodeSignature` returning `Valid` against a trusted root) is Windows-only; on Linux
the tamper check is done via a self-computed content hash. The mechanism is identical; only chain
validation needs a Windows host.
