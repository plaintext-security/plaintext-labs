# Lab 09 — Purple-Team a Detection

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/09-detection-testing
make up
```

Run `make demo` to execute the full purple-team loop: four atomics
(T1059.001 encoded command, T1547.001 run-key persistence, T1003.001 LSASS
access, plus a benign FP test) fire against three Sigma rules using an
in-process matcher — no SIEM required. Each atomic produces an event record
that mirrors what Sysmon would capture on a real Windows endpoint; you see
FIRED / MISSED / FALSE-POSITIVE results and the coverage summary.

For real host testing: install
[Invoke-AtomicRedTeam](https://github.com/redcanaryco/atomic-red-team/wiki/Installing-Invoke-AtomicRedTeam)
on your own Windows lab VM and wire it to your SIEM from module 06.

## Scenario
Fire a real attacker technique and find out whether your detection actually catches it — then tune it.

> Run atomics only on your own lab host.

## Do
1. [ ] Pick an ATT&CK technique your module 08 detection targets, and run its Atomic test on your lab
   host.
2. [ ] Check your telemetry/SIEM: did the detection fire? If not, *why* (missing telemetry, wrong
   field, wrong logic)?
3. [ ] Fix the gap, re-run, and confirm it now fires.
4. [ ] Run a benign workload and measure false positives; tune until the signal is clean.

## Success criteria — you're done when
- [ ] You fired a real technique and confirmed (or fixed) that your detection catches it.
- [ ] You measured and reduced false positives.
- [ ] You can state your detection's coverage and its blind spots.

## Deliverables
`detection-test.md`: the technique, the before/after of your detection firing, and your tuning
decisions.

## AI acceleration
Have a model help diagnose why a detection missed — then verify the fix by re-running the atomic. The
model hypothesises; the test confirms.

## Connects forward
Validated detections roll up into coverage mapping (module 10); the purple-team loop is the heart of
detection engineering.

## Marketable proof
> "I purple-team detections — fire real ATT&CK techniques with Atomic Red Team, validate they catch
> the behaviour, and tune out false positives."

## Automate & own it
**Required.** Script the loop — run an atomic, query the SIEM, report fired / not-fired (AI drafts,
you verify the query); commit it as a repeatable detection test.

## Stretch
- Chain several atomics for one technique and confirm your detection catches all the variants, not
  just one.
