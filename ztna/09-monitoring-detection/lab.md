# Lab 09 — Detect the credential-compromise login in a Zero Trust access log

> **Hands-on lab.** Environment: `plaintext-labs/ztna/09-monitoring-detection`.
> Objective: **write a Sigma rule that fires on the one anomalous *authenticated* access and stays quiet
> on the benign majority**, then turn it into a measured control (held-out eval + regression gate) and
> add a posture-drift detector. Target: **~90–120 min**, one finish line. This is a **reference lab** —
> one command stands up the container.

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **The access log is the detection surface now.** | ZT logs *every* request with identity + device + country + result — you detect anomalous *authenticated* access, not edge breaches. |
| 2 | **The dangerous event SUCCEEDED.** | `lchen`'s `access_allowed` from **NG** is the catch; the loud **RO** `auth_failed` flood is not — a stolen token *passes* auth. |
| 3 | **A rule is a hypothesis on a benign stream.** | `selection` says what's interesting; `not filter` (the operating-country allowlist) is what keeps it off the benign majority. |
| 4 | **The demo set can't prove a detection.** | You tuned on it — it's a memorised exam. Grade on a **held-out** corpus the rule never saw. |
| 5 | **Recall is load-bearing; gate both ways.** | A missed compromise can be a breach; an FP costs minutes. A gate you've only seen *pass* isn't a gate. |
| 6 | **"Trust nothing" is an over-time posture.** | Token-creep, accreted exceptions, disabled posture checks erode it silently — declare → observe → diff → reconcile catches it. |

*(If you can explain all six cold at the end — especially #2 — you've got the objective.)*

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [detection-surface section](README.md#the-detection-surface-every-request-is-now-a-labelled-log-line)
> and [hypothesis-on-a-benign-stream](README.md#a-detection-is-a-hypothesis-on-a-benign-stream).

---

## Warm-up — answer before you run anything (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. Two events in these logs come from outside the operating countries: a **RO** `auth_failed` flood and
   a single **NG** `access_allowed`. Which one is the real attack, and why is the loud one the *safe*
   one to have missed?
2. Your geo-rule fires correctly on the NG event in the demo set. Name the one reason that number still
   doesn't tell you whether the rule is any good.

---

## Setup

This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ztna/09-monitoring-detection
make up      # build + start the container (sigma-cli + the offline matcher detect.py)
make demo    # fire the worked unexpected-country rule against the bundled ZT access logs
make shell   # drop into the container to work
make down    # stop it when you're done
```

Two more targets point at **your** rule once you write it:

```bash
make detect RULE=examples/zt-unexpected-country.yml   # run any rule against data/access-logs.jsonl
make convert RULE=examples/zt-unexpected-country.yml  # compile a rule to Splunk SPL via sigma-cli
```

The container bundles `sigma-cli`, the offline teaching matcher `detect.py` (adapted for ZT access-log
structure), the worked rule in `examples/zt-unexpected-country.yml`, and the data:

- `data/access-logs.jsonl` — **20 real-shaped structured access events** (Pomerium/Cloudflare
  Access-shaped JSONL) with anomalies planted: one unexpected-country `access_allowed`, a six-event
  `auth_failed` flood, and a growing bulk-export volume. This is the set you write and tune against.

> **Authorization note.** Everything here runs locally against bundled data you own — no external
> targets, no authorization needed. This is honor-system: the eval gate and drift loop you build are a
> regression guard for *you*, not a grader. (Later modules stand up real services you *do* attack —
> there the rule binds: only test systems you own or have explicit written permission to test.)

---

## Build it — read a little, do a little

### Step 1 — Find the anomalies by eye (before any tool)

**Concept (30 sec):** Flight-card #1. In a ZT log every request is a labelled line, so the anomalies are
*readable* — you don't need a tool to spot them. Open the log and look at `event_type`, `country`, and
`bytes_sent`.

**Do it:** `make shell`, then read `data/access-logs.jsonl`. Find (a) the single `access_allowed` from a
country that isn't US/CA/GB/DE/AU, (b) the burst of `auth_failed` events from one foreign IP, and (c)
the `access_allowed` events whose `bytes_sent` climbs into the hundreds of thousands.

> **▸ On track if:** you can name the NG event — `user=lchen@corp.com`, `service=data-api`,
> `country=NG` — the six-event **RO** `auth_failed` flood for `jdoe@corp.com`, and the three growing
> `hr-portal` `/employees/export` events (187k → 234k → 312k bytes) for `msmith`. Note that `lchen`
> accessed legitimately from **US** minutes *before* the NG hit — that's an impossible-travel pair.

### Step 2 — Fire the worked rule

**Concept (30 sec):** Flight-card #2 + #3. The worked rule is `selection: event_type = access_allowed`
`and not filter: country in [US,CA,GB,DE,AU]` — a *successful* access from outside the operating set.
It targets MITRE ATT&CK **T1078 (Valid Accounts)**: credential compromise looks like a valid login, not
a failed one.

**Do it:** run `make demo` (or `make detect RULE=examples/zt-unexpected-country.yml`). Read the `[HIT]`
line and confirm it's the NG event — *not* the RO flood.

> **▸ On track if:** the output shows **exactly one hit** —
> `[HIT] line 15: 2026-06-08T10:08:14Z  user=lchen@corp.com  country=NG  service=data-api  type=access_allowed`
> — and `Matched 1 of the events`. The RO `auth_failed` events do **not** fire, because `selection`
> requires `access_allowed`. That silence on the loud flood is the point: you caught the token that
> *passed*, not the ones that failed.

### Step 3 — Prove the filter is load-bearing

**Concept (30 sec):** Flight-card #3. The rule is a hypothesis on a benign stream; `not filter` is what
keeps it off the benign majority. Take the filter away and see what "no filter" actually means.

**Do it:** copy the rule to `my-rule.yml`, delete the `filter:` stanza *and* the `and not filter` from
`condition:` (leaving `condition: selection`), then `make detect RULE=my-rule.yml`.

> **▸ On track if:** with the filter gone the rule now matches **13 events** — every `access_allowed`
> in the file — i.e. it fires on the entire benign population and is useless. Restore the filter and
> you're back to 1. That contrast *is* the lesson: the allowlist is the detection.

### Step 4 — Compile it to a real SIEM query

**Concept (30 sec):** You write a Sigma rule *once*, as vendor-neutral code; `sigma convert` compiles it
to whatever backend the org runs. That portability is why detection-as-code beats hand-writing SPL.

**Do it:** run `make convert RULE=examples/zt-unexpected-country.yml` and read the emitted Splunk query.

> **▸ On track if:** you get an SPL query for the same logic (or a clear "conversion requires a matching
> pipeline" note — the ZT `product: ztna` logsource has no stock Sigma pipeline). Either way you've seen
> the same rule targeting a real backend, not just the offline matcher.

---

## Prove the control (your finish line)

Run the one check that proves the detection is a control, not an anecdote:

> **The proof:** your unexpected-country rule fires on **exactly the NG `access_allowed`** (the
> credential-compromise catch) and is **silent on the RO `auth_failed` flood and the in-country bulk
> export** — one high-fidelity hit, zero benign noise. Confirm `make detect RULE=<your rule>` prints
> `Matched 1` on the demo set and that the single hit is `lchen` / NG.

*If your rule also flags the RO flood, you're keying on failed auth and will miss real credential
compromise. If it flags the exports, your `selection` is too broad. Either way, one of the rule and the
threat model is wrong — fix the rule.*

---

## Recall check — close the doc, answer from memory (3 min)

1. Which event is the real attack — the RO `auth_failed` flood or the NG `access_allowed` — and why is
   the loud one the safe one to miss?
2. What does removing the `filter` stanza do to the hit count, and what does that prove about where the
   detection actually lives?
3. Why can't the demo set tell you whether your rule is good — and what fixes that?

Missed one? Re-run the step that built it, or pull the
[module reveal](README.md#a-detection-is-a-hypothesis-on-a-benign-stream) — then re-answer.

---

## Deliverables

- **`zt-unexpected-country.yml`** (your version) — the committed Sigma rule that fires on the NG
  credential-compromise event and stays quiet on the benign majority, mapped to T1078.
- **`heldout/corpus.jsonl`** — your held-out labelled corpus (built in *Automate & own it*): the anomaly
  variants (compromise login + an impossible-travel pair) and the benign near-misses (logged business
  trip, VPN egress, datacenter-region cloud job), each labelled `anomalous`/`benign` and justified.
- **`eval.py`** + **`drift.py`** + **`baseline/zt-posture.yml`** — the scored/gated eval and the
  declare → observe → diff → reconcile drift loop.
- **`detection.md`** — your notes: the anomalies found by eye, the near-misses and why each is hard, the
  metric choice (and why recall), and the ZT-changes-detection analysis.

*Lab artifacts (raw log exports, keys) stay out of commits — reference them, don't commit them.*

## Automate & own it

**Required.** The shipped env fires the detection; *you* build the two things that turn it into a
control — this is the automation, not an add-on.

1. **`eval.py` + a regression gate.** Build a **held-out** `heldout/corpus.jsonl` — events the rule was
   *never* tuned on, each labelled `anomalous`/`benign`, deliberately stocked with the hard near-misses
   (legit travel, VPN egress, datacenter cloud job) and the anomaly variants (compromise login,
   impossible-travel pair). Score your rule into precision / recall / FP-rate, and **exit non-zero when
   recall drops below your floor OR FP-rate climbs past your ceiling** — a unit test for a detection.
   Prove it **both ways**: GREEN on the good rule, RED on a deliberately too-narrow copy (drops a country
   variant → recall falls) and a too-broad copy (drops a filter entry → fires on legit travel).
2. **`drift.py` + `baseline/zt-posture.yml`.** Declare the intended posture as data
   (`max_token_lifetime_minutes`, allowed `policy_exceptions`, enforced `posture_checks`). Then mutate a
   copy three ways — token-lifetime creep (15 min → 8 hrs), an accreted contractor allow-exception, a
   posture check flipped to `log-only` — diff observed against baseline, **report all three deltas and
   exit non-zero**, then reconcile and confirm zero deltas / exit 0.

Have a model draft the confusion-matrix arithmetic and the JSON diffing — then **own the parts it gets
wrong**: the metric is **recall on anomalies**, not accuracy; **you** label every held-out near-miss by
hand (a model labelling its own test set is the contamination this whole module guards against); the
gate must fail **closed** when the score is missing; and the drift baseline is *your* judgment from the
threat model, not a model's plausible default. Commit `eval.py`, `drift.py`, `baseline/zt-posture.yml`,
`heldout/corpus.jsonl`, the rule, and `detection.md`.

## Definition of done (`zt-monitoring-detection` ✅)

- [ ] `make demo` fires on the NG `access_allowed` (`lchen`, `Matched 1`) and stays silent on the RO
  `auth_failed` flood — you can explain *why* the loud events don't fire.
- [ ] You proved the filter is load-bearing: removing it matches **13** events; restoring it returns to 1.
- [ ] `eval.py` scores your rule against a **held-out** corpus (precision/recall/FP-rate), and you can
  state its recall and FP-rate — not just "it fired in the demo."
- [ ] The gate is GREEN on the good rule and you have **seen it go RED** on *both* a too-narrow and a
  too-broad copy (recall floor breached / FP-rate ceiling breached).
- [ ] `drift.py` detects all three posture drifts, reports the deltas, exits non-zero, then reconciles to
  zero deltas / exit 0.
- [ ] `detection.md` answers: why `auth_failed` is higher-fidelity in ZT than at a perimeter; what a
  *valid-token* attacker looks like in these logs and which field is your best signal; and which drift
  would most weaken your Stage-1 detection (hint: long token lifetimes).

## Connects forward

The ZT access-log structure you detect against is the output of the identity-aware proxy from Module 06,
enriched by microsegmentation flow logs (Module 07) and policy-as-code decision logs (Module 08). A
production deployment feeds all three to one SIEM and writes detections *across* them — a single
unauthorized access from a non-compliant device produces correlated signals in the proxy log, the
flow-drop log, and the policy-decision log at once. That correlation is the ZT detection advantage. The
drift detector here is the same discipline you'd point at Module 08's policy-as-code to catch a
default-deny baseline quietly accreting allow rules.

## Marketable proof

> "I write Sigma detections against Zero Trust access logs — catching the credential-compromise login
> that a perimeter never sees — **prove them on a held-out corpus** with a precision/recall scorecard and
> a CI regression gate that fails on a too-broad or too-narrow rule, and I run a **drift detector** that
> catches the Zero Trust posture itself eroding over time (token-lifetime creep, accreted
> allow-exceptions, disabled posture checks) and reconciles it back to baseline."

## Stretch

- Add an **impossible-travel** detection: two `access_allowed` events for one user/`session_id` from
  countries too far apart for the time delta (the lab's `lchen` US→NG pair is your first case). Add
  labelled cases to the held-out corpus and give the rule its own recall floor.
- Extend `drift.py` to emit a **maturity score** mapped to CISA ZTMM levels (the further observed posture
  is from baseline, the lower the maturity) and gate the build below a maturity floor.
- Convert `zt-unexpected-country.yml` to Elastic EQL via `sigma convert` and check the field mapping
  against a real ZT proxy's published access-log field names.
