# Lab 13 — Hunt Malicious PowerShell in Script Block Logs

*Hands-on lab · [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/13-powershell-logging-hunting
make up        # build + start the container (PowerShell 7 + the hunt harness)
make demo      # worked hunt: flag the malicious script blocks in the bundled 4104 log
make shell     # drop into a PowerShell prompt to hunt interactively
make down      # stop it
```

The container bundles `hunt.ps1` (a small, legible hunt harness) and `data/scriptblock-4104.json` — nine
real-shaped **Event ID 4104** records exported from the fictional **Meridian Financial** estate. Five are
malicious (the cradles, encoding, AMSI tamper, and obfuscation from Offensive Module 15); the rest are
routine administration, including one borderline download that you must *not* over-flag.

> Everything runs locally against bundled data you own. No external targets, no authorisation needed.

## Scenario
A finance workstation (`FIN-WKSTN-07`) ran something that tripped an analyst's instinct. You have the
host's PowerShell Operational log. You'll separate the malicious script blocks from normal admin work,
turn your reasoning into a reusable rule, and — critically — make sure that rule doesn't drown the SOC in
false positives on legitimate downloads.

## Do
1. [ ] `make demo` and read the output: it flags five of the nine script blocks. Open
   `data/scriptblock-4104.json` and find the one downloading event it did **not** flag — what's different
   about it? (Look at the host it pulls from and whether it executes in memory or saves to disk.)
2. [ ] **Learn the field.** Confirm that the malicious blocks are caught on the `ScriptBlockText` field
   even when obfuscated — find the `[char]`-rebuilt entry and explain why 4104 still shows intent.
3. [ ] **Write your own hunt.** Pick a malicious behaviour the demo's indicators *don't* yet name (e.g.
   the AMSI-tamper string, or an in-script `FromBase64String` followed by `IEX`) and add it as a new
   indicator. Confirm it fires on the right block.
4. [ ] **Tune for false positives.** Justify, in one line each, why the benign admin events (an internal
   patch download, an AD query, a process listing) should *not* fire — and adjust any indicator that
   would catch them. A rule that flags every download is a failure here.
5. [ ] **Make it portable.** Express your best indicator as a Sigma rule for the
   `Microsoft-Windows-PowerShell/Operational` 4104 channel — the same detection-as-code shape from Module
   08, ready to run at scale (e.g. with Chainsaw).

## Success criteria — you're done when
- [ ] You can name why the internal-host, save-to-disk download is benign while the in-memory cradle is not.
- [ ] Your added indicator fires on its target malicious block and on none of the benign ones.
- [ ] You have a Sigma rule for the 4104 channel expressing one of your detections.
- [ ] You've written a one-line FP justification for each benign event.

## Deliverables
`powershell-hunt.md` (the verdict per event + your FP reasoning) and `powershell-abuse.yml` (your Sigma
rule). Commit the rule — that's detection-as-code. Don't commit raw exported event logs; reference them.

## Automate & own it
**Required.** Turn your hunt into a reusable function or rule and gate it: add a tiny check (a Pester test
or a CI step) that runs your detection against the bundled sample and **fails** if it stops catching the
known-malicious blocks *or* starts catching the benign ones — a regression test for your detection. Have a
model draft the Sigma rule and the test; **you read every line** and confirm both behaviours against the
real sample before trusting them.

## AI acceleration
Have a model triage the batch — classify each script block and explain the suspicious ones — then verify
its calls against the sample yourself, especially the benign download it's most likely to over-flag. The
model accelerates triage; you own the false-positive line.

## Connects forward
This is the defensive half of a pair with **Offensive Module 15 (PowerShell Tradecraft)** — you're hunting
exactly what it produces. Your Sigma rule plugs straight into **Module 08 (Detection-as-Code)** and is
tested under fire in **Module 09 (Detection Testing)**.

## Marketable proof
> "I enable and hunt PowerShell Script Block Logging — I catch obfuscated, in-memory PowerShell in 4104
> records and write tuned, false-positive-aware Sigma rules for it."

## Stretch
- Convert your bundled-JSON hunt to run over a real `.evtx` with [Chainsaw](https://github.com/WithSecureLabs/chainsaw)
  and a Sigma ruleset — the production path.
- Add detection for a PowerShell **v2 downgrade** (`-Version 2`) attempt and explain why it's high-signal.
