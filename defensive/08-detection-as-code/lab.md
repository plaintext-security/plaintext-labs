# Lab 08 — Write and Test a Sigma Detection

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/defensive/08-detection-as-code
make up        # build + start the container (sigma-cli + the matcher)
make demo      # see the worked example: convert a rule to SPL, then fire it at sample telemetry
make shell     # drop into the container to work
make down      # stop it when you're done
```

The container bundles `sigma-cli` (the real converter) and a small **teaching matcher**
(`detect.py`) so a rule can fire offline, with no SIEM to stand up. Sample telemetry lives in
`data/events.jsonl` — six real-shaped Windows process-creation events from the fictional
**Meridian Financial** estate, one of which is malicious. The worked example is in `examples/`.

> Everything runs locally against bundled data you own. No external targets, no authorization
> needed for this one.

## Scenario
A Meridian analyst flags that Word spawned PowerShell on a finance workstation. You'll write a
portable detection for the technique behind it — **encoded PowerShell (ATT&CK T1059.001)** — prove
it fires on the real event, and reason about where it would false-positive. Then you'll do it as
code: the rule in git, converted to a SIEM query, linted in CI.

## Do
1. [ ] `make demo` and read the output: the example rule converts to a Splunk query *and* matches
   exactly one event. Open `data/events.jsonl` — which event, and what made it stand out? (Look at
   `ParentImage`.)
2. [ ] Now write your own. Copy `examples/encoded_powershell.yml` to `detection.yml` and **make it
   yours**: pick a *different* signal in the malicious event (the `ParentImage` of an Office app
   spawning PowerShell is a strong one) and write the `selection` for it. Tag it with the ATT&CK
   technique.
3. [ ] `make detect RULE=detection.yml` — confirm your rule fires on the malicious event.
4. [ ] `make convert RULE=detection.yml` — convert it to Splunk SPL. This is the query you'd
   actually deploy.
5. [ ] **Reason about false positives.** Would your rule fire on any of the benign events? Could the
   ` -enc ` fragment collide with a legitimate ` -Encoding ` argument? Write down what you'd tighten.

## Success criteria — you're done when
- [ ] Your `detection.yml` fires on the malicious event and **not** on the five benign ones.
- [ ] It's tagged with the correct ATT&CK technique (T1059.001).
- [ ] It converts cleanly to a SIEM query with `make convert`.
- [ ] You've written down its false-positive behaviour and what you'd tune.

## Deliverables
`detection.yml` (your Sigma rule) + `detection.md` (the technique, your field logic, your FP
reasoning). **Commit the rule to git** — that's the whole point of detection-as-code.

## Automate & own it
**Required.** Add a tiny CI check that lints and converts every rule on commit — a GitHub Actions
workflow that runs `sigma convert` (or `sigma check`) over your `*.yml` rules and fails on a broken
one. Have a model draft the workflow; **you read every line** and confirm it actually runs before
trusting it. Commit it next to the rule. Now a bad rule can't merge — that's detection-as-code for real.

## AI acceleration
Have a model draft the Sigma rule from your description of the event — it's good at the YAML shape.
Then *you* run it through `make detect` against the real sample and `make convert` to a query. The
model writes; you test, tag, and own it. A rule it drafted that you never fired is a guess, not a
detection.

## Connects forward
This rule gets *tested under fire* in module 09 (detection testing) and mapped for coverage in
module 10 (ATT&CK coverage); detection-as-code is the spine of the whole track.

## Marketable proof
> "I write detection-as-code in Sigma — version-controlled, ATT&CK-tagged, converted to my SIEM,
> and tested against real attack telemetry in CI."

## Stretch
- Add a `filter` and switch the rule to `condition: selection and not filter` to suppress a known
  benign case (the matcher supports it) — then prove the FP is gone.
- Convert the same rule to a second backend and confirm it still expresses the same logic — the
  "write once, detect anywhere" promise.
