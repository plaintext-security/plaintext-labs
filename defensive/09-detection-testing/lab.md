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

`make demo` then runs the **eval harness**: it scores the rules against a
**held-out** labelled corpus (`heldout/corpus.jsonl` — known-malicious and
known-benign events the rules were never tuned on) and applies a **regression
gate**. You watch the gate go GREEN on the good rules (recall 100%) and RED on
a deliberately-regressed ruleset (`heldout/rules-regressed/`, recall 70% — it
silently stopped catching the `-enc` short form). `make eval` runs just the
scorecard + gate on the good rules; `make gate` proves the gate catches the
regression (exits non-zero). All offline and deterministic — no SIEM, no
network. This is honor-system: the gate is a regression guard, not a grader.

**Opt-in: score the shipped rules over REAL telemetry — no Windows host.**
`make fetch-events` clones [EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES)
(real Sysmon captures for these techniques) and converts the matching events into
`heldout/corpus-real.jsonl`; `make eval-real` then scores the **same Sigma rules**
over them. You'll watch the run-key rule fire on a genuine `…\CurrentVersion\Run`
write — and the LSASS rule **miss**, because real `GrantedAccess` is `0x1fffff`,
not the textbook `0x1410` the rule assumes. That gap between your tuning fixtures
and real telemetry is the whole point of detection testing (see `PROVENANCE.md`).
The committed synthetic corpus stays the deterministic gate; this adds real events.

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
5. [ ] **Build a held-out test corpus.** Assemble labelled events your rule was *never tuned on*:
   known-malicious samples it must catch (include variants — the `-enc` short form *and* the
   long `-EncodedCommand`) and known-benign lookalikes it must NOT fire on (a signed updater
   writing a Run key, a legit `certutil -decode`). Keep it separate from your demo/tuning atomics —
   that wall is what makes the score honest. See `heldout/corpus.jsonl` for the shape.
6. [ ] **Score it.** Run `make eval` to get a scorecard — recall (caught attacks / all attacks) and
   FP-rate over the held-out set, not just "it fired in the demo." A rule with 95% accuracy that
   misses the rare attack is worthless; chase recall, then push FP-rate down without losing it.
7. [ ] **Tune and re-score.** When recall < your floor, find the missed events (the scorecard lists
   them), widen the rule, and re-run until the gate passes — then confirm you didn't open new FPs.

## Success criteria — you're done when
- [ ] You fired a real technique and confirmed (or fixed) that your detection catches it.
- [ ] You measured and reduced false positives.
- [ ] You can state your detection's coverage and its blind spots.
- [ ] You built a held-out corpus and have a scorecard (recall + FP-rate), not just a demo anecdote.
- [ ] Your regression gate is GREEN on the good rule and you have *seen it go RED* on a regression —
      a gate you've only watched pass isn't a gate.

## Deliverables
`detection-test.md`: the technique, the before/after of your detection firing, and your tuning
decisions. Plus your **held-out corpus**, **`eval.py` scorecard**, and the **regression gate**
(the `make eval` target) — committed so the detection can't silently regress.

## AI acceleration
Have a model help diagnose why a detection missed — then verify the fix by re-running the atomic. The
model hypothesises; the test confirms. Ask it to draft *adversarial* held-out events — benign
activity crafted to look malicious (a signed updater touching a Run key) — then label each yourself
against the real technique it mimics. A model labelling its own test set is the contamination this
whole module guards against; you own the labels and the metric.

## Connects forward
Validated detections roll up into coverage mapping (module 10); the purple-team loop is the heart of
detection engineering.

## Marketable proof
> "I purple-team detections — fire real ATT&CK techniques with Atomic Red Team, validate they catch
> the behaviour, tune out false positives, and gate each rule against a held-out corpus in CI so it
> can't silently regress."

## Automate & own it
**Required.** Don't stop at scripting the loop — turn your detection into a **regression gate** so it
can't silently rot. Wrap the loop in an eval that scores your rule against your **held-out corpus**
and **exits non-zero when recall drops below your floor** (or FP-rate climbs past your ceiling) —
exactly as a unit test fails on a broken function. Prove it both ways: GREEN on the good rule, and
*RED on a deliberately-regressed copy* (the lab ships `heldout/rules-regressed/` and a `make eval` /
`make gate` you can copy). AI drafts the metric arithmetic and the scorecard table; **you own the
metric choice (recall on the malicious class, not accuracy), the held-out wall, and the gate's
fail-closed direction.** Commit `eval.py` + the corpus + the gate alongside the rule. (Honor system —
this gate guards *you* against regressions; there's no grader.)

## Stretch
- Chain several atomics for one technique and confirm your detection catches all the variants, not
  just one.
