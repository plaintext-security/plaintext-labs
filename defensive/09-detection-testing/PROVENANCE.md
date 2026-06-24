# Provenance — Module 09, Detection Testing (Purple Team)

## What ships in this repo

The `atomics/` here are **synthetic emulators**, not the real attacker tooling. Each
produces a Sysmon-shaped event record so the bundled Sigma rules can be exercised
**offline, deterministically, in a Linux container** — no Windows host, no SIEM, no
network. They use neutral placeholder naming (`CORP\auser`, `deploy`). The held-out
corpus (`heldout/corpus.jsonl`) is likewise curated, labelled, and synthetic.

This is honest by design: the emulators are clearly labelled as stand-ins, and each
one **points at the genuine Atomic Red Team test it mirrors**. The real validation
move — running the actual atomic on a Windows lab host and watching your SIEM — is
in `lab.md`.

## The real tests each emulator mirrors

Atomic Red Team (https://github.com/redcanaryco/atomic-red-team) — Red Canary's
library of small, reproducible ATT&CK technique tests. **License: MIT.**

| Emulator (this repo)                | Real Atomic Red Team atomic (verified)                                                        |
|-------------------------------------|-----------------------------------------------------------------------------------------------|
| `atomics/T1059_001_encoded_command.py` | **T1059.001** — PowerShell (encoded command) — https://github.com/redcanaryco/atomic-red-team/tree/master/atomics/T1059.001 |
| `atomics/T1547_001_run_key.py`         | **T1547.001** — Registry Run Keys / Startup Folder — https://github.com/redcanaryco/atomic-red-team/tree/master/atomics/T1547.001 |
| `atomics/T1003_001_lsass.py`           | **T1003.001** — OS Credential Dumping: LSASS Memory — https://github.com/redcanaryco/atomic-red-team/tree/master/atomics/T1003.001 |
| `atomics/T1059_001_benign_fp.py`       | (no atomic — a benign false-positive control: a legitimate base64-over-SSH admin task)        |

The T1059.001 directory includes published encoded-command tests (e.g. the
`-EncodedCommand` parameter-variation tests and *"PowerShell Command Execution"*,
GUID `a538de64-1c74-46ed-aa60-b995ed302598`), which is exactly the behaviour our
encoded-PowerShell emulator stands in for.

## Running the genuine tests

For real host validation, install
[Invoke-AtomicRedTeam](https://github.com/redcanaryco/atomic-red-team/wiki/Installing-Invoke-AtomicRedTeam)
on **your own Windows lab VM**, run the atomic for the technique above, and confirm
your detection fires in the SIEM you stood up in module 06. Run atomics only on a
host you own.

## One-line citation

> Atomic Red Team (T1059.001, T1547.001, T1003.001),
> https://github.com/redcanaryco/atomic-red-team (MIT). The `atomics/` in this lab
> are synthetic emulators of these tests for offline, deterministic CI.
