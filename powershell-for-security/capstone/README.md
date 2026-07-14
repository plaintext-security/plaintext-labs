# Capstone — Ship `Vigil`

The capstone of **Track 13 · PowerShell for Security**. This is a **starter scaffold**, not a solution:
it gives you the module skeleton, test/eval/signing shapes, and acceptance checks. You integrate the nine
modules' work into one shipped `Vigil` — typed, tested, gated, signed — and grade it against
[`rubric.md`](rubric.md).

```bash
make up       # build the pwsh 7 + PSScriptAnalyzer 1.22.0 + Pester 5.6.1 container
make accept   # structural checks: manifest, explicit exports, analyzer, stub progress
make test     # the Pester suite (fill in the -Pending stubs)
make eval     # the detection eval (implement eval.ps1)
make shell    # drop into pwsh
make down     # stop when done
```

## What to build (integrate the phases)

`Vigil` is one module that ingests real Windows telemetry, normalizes it to typed objects, enriches it
concurrently and safely, serves a least-privilege hunt endpoint, is callable over MCP, detects a real
PowerShell attack, and is **eval-gated, supply-chain-audited, and signed.** The scaffold's stubs map to the
track:

| Stub | Module | What it must become |
|---|---|---|
| `Get-VigilEvent` | 03 | `Get-WinEvent` server-side filtering over real `.evtx`, typed objects out |
| `ConvertTo-VigilEvent` | 02 | advanced function, `[OutputType]` + validation, normalizes to a typed `VigilEvent` |
| `Invoke-VigilEnrichment` | 04 | concurrent enrichment, throttle + backoff, no runspace races |
| `Get-VigilDetection` | 08/09 | the detonated-and-detected technique, as a classifier the eval scores |
| `eval.ps1` | 09 | held-out scorecard + CI regression gate |
| `tests/Vigil.Tests.ps1` | 09 | real `Pester` (mocks + unhappy paths + coverage floor) |
| signing loop | 09 | pinned installs + sign/verify (see Module 09's `sign.ps1`) |

Not shown as stubs but required by the rubric: the **least-privilege endpoint** (Module 06, JEA — Windows
VM, assessed-not-demonstrated in the container), the **MCP surface** (Module 07), and the **safe
external-process** discipline (Module 05, no `Invoke-Expression`).

## Ground it in real data

The rubric's bar is a genuinely useful tool fed **real** telemetry — a public `.evtx` corpus
([EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES)), real Sysmon output, or a free
feed like [abuse.ch](https://abuse.ch/). Put your held-out labelled samples under `data/heldout/`.

## Ownership of AI code

Ship a `WRITEUP.md` that names what AI generated vs. what you changed and why, and points to at least one
bug or risk you caught in generated code and fixed. Per the honor system, **the committed module is the
proof** — there is no grader. Grade yourself against [`rubric.md`](rubric.md); **Proficient is the bar to
ship.**

## Authorization

Only test systems you own or have explicit written permission to test. The detection/detonation work uses
intentionally vulnerable targets and bundled samples only.
