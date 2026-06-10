# Lab 15 — Build a PowerShell Cradle and Watch What It Logs

*Hands-on lab · [← Back to the module concept](README.md)*

## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/offensive/15-powershell-tradecraft
make up        # build + start the payload host (web) and the attacker box (attacker)
make demo      # worked example: cradle → encoded → obfuscated → the 4104 it all emits
make shell     # drop into a PowerShell prompt on the attacker box
make down      # stop it
```

The lab is two containers running PowerShell 7: `web` stages a **benign** payload over HTTP, and
`attacker` is where you build and fire the cradle against it. `tradecraft.ps1` holds reusable helpers
(encode / obfuscate / emit-4104) you'll extend. Everything runs PowerShell faithfully at the language
level; AMSI is a Windows runtime feature, so the AMSI step below is documented against a Windows VM.

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Scenario
A phish has landed you code execution as `MERIDIAN\jsmith` on a finance workstation. You'll reproduce
the standard PowerShell first moves — stage a payload, run it in memory, then encode and obfuscate the
launcher — and at each step record exactly what an analyst would see. The deliverable is an operator's
note that pairs each technique with its telemetry, which Defensive Module 13 then hunts.

## Do
1. [ ] Run `make demo` once to see the whole arc end-to-end. Then rebuild it yourself from `make shell`
   so you can explain each step — the demo is your reference, not your answer.
2. [ ] **Stage and run in memory.** Using the `web` container as your payload host, fetch and execute the
   payload *without writing it to disk*. (Which one-liner is the canonical in-memory cradle? Confirm the
   payload's marker prints.)
3. [ ] **Encode the launcher.** Produce the `-EncodedCommand` form of your cradle, then decode it back to
   prove the encoding is reversible. (What encoding and text representation does `-enc` actually use?)
   Note what an analyst sees on the command line versus in the decoded script block.
4. [ ] **Obfuscate without changing behaviour.** Transform the launcher so its bytes no longer match a
   naive string rule, but it still runs identically. (Concatenation and `[char]`-code rebuilding are two
   families — `tradecraft.ps1` has one; add another.) Prove it still executes.
5. [ ] **Find the limit.** Explain — and show with the emitted Event ID 4104 record — why every variant
   above still appears in cleartext at execution. Which detection surface did obfuscation defeat, and
   which did it not?
6. [ ] **AMSI (Windows VM, documented).** On a Windows VM with AMSI enabled, observe a payload being
   blocked, then research one in-memory AMSI bypass and explain why patching `amsiInitFailed` is itself a
   high-signal event. (No container step — reason about the trade-off and record it.)

## Success criteria — you're done when
- [ ] Your cradle executes the staged payload in memory (nothing written to disk).
- [ ] You can produce *and* decode the `-EncodedCommand` form.
- [ ] You have at least one obfuscated launcher that runs identically to the plain one.
- [ ] You can state, with the 4104 evidence, exactly which detection each technique evades and which it doesn't.

## Deliverables
`tradecraft-notes.md`: each technique paired with the telemetry it generates (command line vs. 4104
script block), and your one-paragraph judgement on which is "quietest" and why. **Do not** commit real
payloads or captured logs — reference them.

## Automate & own it
**Required.** Extend `tradecraft.ps1` into a small launcher-builder: given a command, it emits the plain,
encoded, and obfuscated forms **and** the Event ID 4104 record each would generate — the same JSON shape
Defensive Module 13 hunts. Have a model draft an extra obfuscation transform; **you read every line**,
confirm it runs and that you understand what it logs, before committing it. Owning the telemetry your
tooling produces is the whole point.

## AI acceleration
Let a model generate obfuscation variants quickly, then verify each by running it and reading the 4104 it
produces — keep only the ones you understand. A variant you pasted but never tested against the telemetry
is a liability on an engagement, not tradecraft.

## Connects forward
This is the attacker half of a pair: **Defensive Module 13 (PowerShell Logging & Hunting)** hunts exactly
these script blocks in 4104 logs, and **Defensive Module 08 (Detection-as-Code)** writes the Sigma rule
for them. Module 14 (LOLBins) covers the non-PowerShell native-tooling angle.

## Marketable proof
> "I emulate real PowerShell tradecraft — in-memory cradles, encoded and obfuscated launchers — and I can
> explain to a defender exactly what each technique leaves in Script Block Logging."

## Stretch
- Reproduce one of Invoke-Obfuscation's token-level transforms by hand and confirm 4104 still captures the
  reassembled command.
- Chain the cradle to a scheduled-task or registry Run-key persistence (own lab only) and note the
  additional telemetry that creates.
