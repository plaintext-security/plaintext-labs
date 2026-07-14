# Capstone rubric — `Vigil`

Grade your own work against this (peer or reviewer feedback welcome). This is the honor system: **no tool
gates completion — the committed module is the proof.** **Proficient is the bar to ship.** It must be a
genuinely useful tool you own — typed, tested, reviewed line by line, and fed **real data** (a public
`.evtx` corpus like EVTX-ATTACK-SAMPLES, a free threat feed like abuse.ch, or real Sysmon output).

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **Usefulness** | A script that re-implements a one-liner | A module you'd reach for to triage real Windows telemetry | Fills a real gap; handles a hunt workflow end to end |
| **Typed boundaries** | Emits strings; trusts input | Advanced functions with `[OutputType]` + validation; objects out; `PSScriptAnalyzer` clean | Invalid input unrepresentable; LLM output validated like telemetry |
| **Concurrency** | Sequential loop, or a runspace race | `ForEach-Object -Parallel` with a throttle + backoff | Handles rate limits, retries, and partial failure without shared-state races |
| **Tests & eval** | None, or happy-path only | `Pester` v5 + a detection eval scorecard with a CI regression gate | Coverage gate + a held-out corpus; the gate blocks a planted regression |
| **Safety** | `Invoke-Expression`; plaintext creds | No `iex`/string-built commands; secrets via `SecretManagement`; JEA least-privilege endpoint | Red-teamed against a real PowerShell technique; residual-risk note |
| **Ownership of AI code** | Pasted AI output unread | Write-up names what AI generated vs. what you changed and why | Demonstrates a caught bug/risk in generated code you fixed and explained |

## How to self-assess each dimension

- **Usefulness** — would *you* reach for this to triage a real incident? If it only replays a demo, it's Developing.
- **Typed boundaries** — `Get-Command -Module Vigil` shows advanced functions; outputs are objects
  (`| Get-Member` shows a type, not a string); `Invoke-ScriptAnalyzer` is clean. LLM/MCP output is validated
  with the same typed discipline as telemetry (Module 07).
- **Concurrency** — enrichment runs in parallel with a bounded `-ThrottleLimit`; results collect in a
  thread-safe sink (no `@()` with `+=`); a transient failure retries with backoff, not a whole-run poison.
- **Tests & eval** — the `Pester` suite has real assertions, at least one `Should -Invoke` mock, and an
  unhappy path; `eval.ps1` scores a **held-out** corpus (never the tuning set) and its regression gate
  **fails** on a planted drop. Coverage is a floor, not your effectiveness claim — say so.
- **Safety** — no `Invoke-Expression` / string-built command lines; external processes are called with
  argument arrays; secrets come from `SecretManagement`; a JEA endpoint exposes only read-only hunt verbs.
  Include a short residual-risk note.
- **Ownership of AI code** — `WRITEUP.md` names what AI wrote vs. what you changed and why, and points to at
  least one bug/risk you caught in generated code (a happy-path test, an eval on the tuning set, an unpinned
  install, a runspace race, an `iex`).

**No silent caps:** where the container can't demonstrate a Windows-only surface (JEA/AMSI enforcement,
Authenticode chain trust), label it *assessed-not-demonstrated* and say what a Windows host would add.
