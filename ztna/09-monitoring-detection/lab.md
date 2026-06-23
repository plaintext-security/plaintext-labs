# Lab 09 — Detection, Eval & Drift in a Zero Trust Environment

*Hands-on lab · [← Back to the module concept](README.md)*

**Type 6 · Reconstruct/Detect (+ Type 13 · Eval Harness, Type 16 · Drift/Steady-State).** You write a
detection against immutable identity-aware access logs, then do the two things that turn a detection
from an anecdote into a control: **measure it** on a held-out corpus behind a regression gate, and
**watch the posture itself for drift** over time. The deliverable is the *scored detection (held-out +
gate) + the drift detector* — not a writeup. No grader; you verify your own work against the observable
success criteria below. (Honor system: the committed rules, corpus, scorecard, gate, and drift loop are
the proof.)

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/09-monitoring-detection
make up         # build + start the container (sigma-cli + the offline matcher + eval + drift)
make demo       # the full loop: detection fires, eval scores + gates, drift detector flags + reconciles
make eval       # just the scorecard + regression gate on the held-out corpus
make gate       # prove the gate catches a too-broad / too-narrow rule (exits non-zero)
make drift      # introduce posture drift, detect it, reconcile to baseline
make shell      # drop into the container to work
make down       # stop it when you're done
```

The container bundles `sigma-cli`, the offline teaching matcher (`detect.py`, adapted for ZT access-log
structure), the eval harness (`eval.py`), and the drift detector (`drift.py`). The data is split into
two deliberately-separate sets:

- `data/access-logs.jsonl` — the **demo/tuning** set: 20 real-shaped structured access events with a few
  anomalies planted, the set you write and tune the rule against.
- `heldout/corpus.jsonl` — the **held-out** labelled corpus: events the rule was *never tuned on*, each
  labelled `anomalous` or `benign`, deliberately stocked with the hard near-misses (legit travel, VPN
  egress, an impossible-travel pair). This is what `make eval` grades against. That wall between the two
  sets is what makes the score honest — score on the tuning set and every number is inflated.

> **Authorization note:** Only test systems you own or have explicit written permission to test.
> Everything here runs locally against bundled data you own — no external targets, no authorization
> needed. This is honor-system: the gate is a regression guard for *you*, not a grader.

## Scenario

An organization has completed its identity-aware-access pilot (Module 06) and every internal service now
logs access events to a central SIEM. The logs are structured JSONL — each event carries user identity,
device, country, service, action, and data volume. The security team wants its leading-indicator
detection — **a valid session authenticated from outside the operating countries (US, CA, GB, DE, AU)**,
the classic credential-compromise signal — *operational and proven* before the production rollout: it must
catch the real anomaly, stay quiet on legitimate travel and VPN egress, and not silently rot. And because
the deployment will run for years, they want a second control entirely: a detector that catches the
*posture* drifting away from the Zero Trust baseline they signed off on.

## Do

### Stage 1 — Write and fire the detection (Type 6)

1. [ ] **Read the demo set.** Open `data/access-logs.jsonl` and note the field structure: `event_type`,
   `user`, `country`, `device_posture`, `bytes_sent`, `session_id`. Find the anomalous events by eye — the
   unexpected-country access and the auth-failure cluster should be visible without running anything.

2. [ ] `make demo`'s first stage fires the example rule (`examples/zt-unexpected-country.yml`) on the
   unexpected-country event. Which log line, which user, which country? This is a `selection and not
   filter` rule — identify which field the `filter` excludes (the operating-country allowlist).

3. [ ] **Understand the filter.** What happens if you remove the `filter` stanza entirely — how many
   events fire? Verify by temporarily removing it and running `make detect RULE=examples/zt-unexpected-country.yml`.
   This is the whole game: the rule is a *hypothesis on a benign stream*, and the filter is what keeps it
   from firing on the benign majority.

### Stage 2 — Measure it on a held-out corpus + gate it (Type 13)

4. [ ] **Prove it's good — on data it has never seen.** `make eval` scores the rule against
   `heldout/corpus.jsonl` (the held-out set, *not* the demo set) and prints a scorecard: precision, recall,
   and FP-rate over labelled `anomalous`/`benign` events. Read the numbers. The held-out set includes the
   near-misses a naive geo-rule fires on and shouldn't — a legit business trip (logged), a developer's
   corporate-VPN egress through another country, a cloud job geolocating to a datacenter region — plus the
   anomaly variants it *must* catch (the compromise login, and an impossible-travel pair). **Recall is the
   load-bearing metric**: a missed credential-compromise can be a breach; a false positive costs minutes.

5. [ ] **See the gate fail both ways.** `make gate` runs the eval against two deliberately-broken copies in
   `heldout/rules-regressed/`: a **too-narrow** rule (it dropped a country variant and now misses an
   anomaly — recall falls below the floor) and a **too-broad** rule (it dropped a filter entry and now
   fires on legit travel — FP-rate climbs above the ceiling). Both must turn the gate RED and exit
   non-zero. Confirm the contrast: GREEN on the good rule, RED on each regression. *A gate you've only seen
   pass isn't a gate.*

6. [ ] **Tune against the held-out failures.** If your own variant of the rule misses an anomaly, the
   scorecard lists the false negatives — widen the rule, re-`make eval`, and confirm you didn't open new
   false positives on the benign near-misses. This is the FP/recall knee, found deliberately.

### Stage 3 — Detect posture drift over time (Type 16)

7. [ ] **Read the baseline.** Open `baseline/zt-posture.yml` — the intended Zero Trust posture *declared as
   data*: `max_token_lifetime_minutes`, the allowed `policy_exceptions` set, and the `posture_checks` that
   must be `enforced`. This is the `t=0` posture the org signed off on.

8. [ ] **Introduce drift and detect it.** `make drift` mutates a copy of the running config three ways —
   *token-lifetime creep* (15 min → 8 hrs), an *accreted allow-exception* (a contractor DB rule that
   outlived the contractor), and a *silently-disabled posture check* (device-compliance flipped to
   `log-only`) — then runs `drift.py` to diff observed config against `baseline/zt-posture.yml`. It must
   report all three deltas and **exit non-zero**. Read the delta report: each line is a Zero-Trust property
   that eroded with no alarm of its own.

9. [ ] **Reconcile to steady-state.** `make drift`'s final step re-applies the baseline and re-runs the
   diff — it must now report zero deltas and exit 0. That detect → diff → report → reconcile loop *is* the
   deliverable; "trust nothing" is the posture you hold, and this is how you hold it.

10. [ ] **Reason about what ZT changes.** In `detection.md`, address: why is `auth_failed` higher fidelity
    in ZT than at a perimeter firewall? What would an attacker with a *valid* token (credential compromise,
    not brute force) look like in these logs, and which field is your best signal? And: which of the three
    drifts would have most weakened your Stage-1 detection's value (hint: long token lifetimes)?

## Success criteria — you're done when

- [ ] `make demo` fires on the unexpected-country event cleanly and runs the full eval + drift loop end to end.
- [ ] `make eval` produces a scorecard (precision/recall/FP-rate) over the **held-out** corpus, and you can
      state the rule's recall and its FP-rate — not just "it fired in the demo."
- [ ] `make gate` is GREEN on the good rule and you have **seen it go RED** on *both* a too-narrow and a
      too-broad rule (recall floor breached / FP-rate ceiling breached).
- [ ] `make drift` detects all three posture drifts (token-lifetime creep, accreted exception, disabled
      posture check), reports the deltas, exits non-zero, and then reconciles to zero deltas / exit 0.
- [ ] Your `detection.md` answers the three ZT-changes-detection questions in step 10.

## Deliverables

- `heldout/corpus.jsonl` — your held-out labelled corpus (or your additions to it): the anomaly variants
  and the benign near-misses, each labelled and justified.
- `eval.py` + the `make eval` / `make gate` targets — the scorecard and the regression gate, proven both
  ways (RED on too-narrow and too-broad).
- `drift.py` + `baseline/zt-posture.yml` + the `make drift` target — the declared baseline and the
  detect → diff → reconcile loop.
- `detection.md` — your notes: the anomalies found by eye, the held-out near-misses and why each is hard,
  the metric choice (and why recall), and the ZT-changes-detection analysis.

Commit all alongside the worked example rule. Lab artifacts (raw log exports, keys) stay out of commits.

## Automate & own it

**Required.** The eval *is* the automation: don't stop at scripting the detection — turn it into a
**regression gate** so the rule can't silently rot. Wrap the scorecard in an eval that scores your rule
against the **held-out corpus** and **exits non-zero when recall drops below your floor OR FP-rate climbs
past your ceiling** — exactly as a unit test fails on a broken function. Prove it both ways (the lab ships
`heldout/rules-regressed/` and `make eval` / `make gate` to copy). Then layer the **drift detector** on
top as the steady-state half: a scheduled `drift.py` that diffs observed posture against
`baseline/zt-posture.yml` and alerts on any delta. AI drafts the metric arithmetic, the scorecard table,
and the JSON diffing; **you own the metric choice (recall on anomalies, not accuracy), the held-out wall,
the gate's fail-closed direction, and the baseline values (set from the threat model, not a model's
default).** (Honor system — the gate and the drift loop guard *you*; there's no grader.)

## AI acceleration

Give a model one log line and the field names and ask for a Sigma rule for "successful access from a
country not in [US, CA, GB, DE, AU]." It produces a working `selection and not filter` pattern fast. Then
test the deny side by hand: the benign near-misses in the held-out corpus (the VPN-egress event, the
logged business trip) are exactly where AI rules fail — they nail the hit case and miss the filter edge
cases. For the eval, have the model *draft* adversarial held-out items, then **label each yourself** against
the real behavior it mimics — a model labelling its own test set is the contamination this module guards
against. For the drift detector, the model writes the diff cleanly, but **you set the baseline**: a model
asked "what's a safe token lifetime?" gives a plausible default; the threat model sets it, and the detector
flags deviations from *that*.

## Connects forward

The ZT access-log structure this module detects against is the output of the identity-aware proxy you built
in Module 06 and would be enriched by microsegmentation flow logs (Module 07) and policy-as-code decision
logs (Module 08). A production deployment feeds all three to one SIEM and writes detections across them — a
single unauthorized access from a non-compliant device produces correlated signals in the proxy log, the
flow-drop log, and the policy-decision log at once. That correlation is the ZT detection advantage. The
drift detector here is the same discipline you'd point at the policy-as-code from Module 08 to catch a
default-deny baseline quietly accreting allow rules.

## Marketable proof

> "I write Sigma detections against Zero Trust access logs, **prove them on a held-out corpus** with a
> precision/recall scorecard and a CI regression gate that fails on a too-broad or too-narrow rule, and I
> run a **drift detector** that catches the Zero Trust posture itself eroding over time — token-lifetime
> creep, accreted allow-exceptions, disabled posture checks — and reconciles it back to baseline."

## Stretch

- Add an **impossible-travel** detection: two `access_allowed` events for one `session_id`/user from
  countries too far apart for the time delta. Add labelled cases to the held-out corpus and extend the
  scorecard so this rule has its own recall floor.
- Extend `drift.py` to emit a **maturity score** mapped to the CISA ZTMM levels (the further the observed
  posture is from baseline, the lower the maturity), and gate the build below a maturity floor.
- Convert `zt-unexpected-country.yml` to an Elastic EQL or Splunk query via `sigma convert` and confirm the
  field mapping against a real ZT proxy's published access-log field names.
