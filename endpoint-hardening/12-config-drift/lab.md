# Lab 12 — Configuration & Posture Drift: Build the Detect → Diff → Reconcile → Alert Loop

*Type 16 · Drift / Steady-State. [← Back to the module concept](README.md)*

**Type 16 · Drift / Steady-State.** You take a host already hardened to a baseline-as-code (the Module-06
playbook), *declare* that baseline, then **introduce real drift** — a package update flips a sysctl, an
operator re-opens `PermitRootLogin`, an added world-writable file — and build the **full steady-state
loop**: a *scheduled* detector that diffs observed state against declared, a **diff that reports *what*
changed and against *which* control** (not a score), **automated reconciliation** back to baseline, and an
**alert on the delta**. The deliverable is the *running loop* — proven by introducing drift and watching it
get detected, named, reconciled, and alerted on — not a one-time scan. No grader; you verify your own work
against the observable success criteria below. (Honor system: the committed loop, the drift-event log, and
the proof captures are the proof.)

## Setup

> **Lab env to be built & validated at promotion.** This is the endpoint track's first first-class Type 16
> and has **no `plaintext-labs` directory built yet** — the **Lab-env spec** at the end of this file is the
> build contract. It reuses Module 06's Ansible-controller-plus-target shape (so it stands up entirely in
> Docker with **zero cloud credentials and zero cost**) and adds the drift-injection, control-named diff,
> reconcile, and alert pieces on top. Until `make up`/`make demo` has actually been run green on a Linux
> runner, treat the first run as the validation pass. Every command below is real and runs on a laptop with
> Docker installed.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/endpoint-hardening/12-config-drift
make up          # Ansible controller + an already-hardened target container (baseline converged at t=0)
make baseline    # converge the target to the declared baseline and confirm zero drift
make drift       # inject 3 realistic drifts (package flips a sysctl, re-opened PermitRootLogin, world-writable file)
make detect      # run the scheduled detector once: control-named diff (what changed, which control)
make reconcile   # re-converge to baseline; prove observed == declared again
make loop         # the full detect -> diff -> reconcile -> alert beat, as the scheduler runs it
make shell       # drop into the controller to run ansible/oscap/osquery by hand
make down
```

`make up` brings up an **Ansible controller** and a **target** host that is already hardened (the Module-06
five-control baseline is converged at start — `t=0`, zero drift). `make drift` plays the role of *the world
acting on the host*: it injects three drifts the way they really happen — a (simulated) package post-install
that flips `net.ipv4.conf.all.rp_filter` back to `0`, an operator who sets `PermitRootLogin yes` in
`sshd_config`, and a dropped world-writable file. The loop's job is to catch all three, name them by
control, pull them back, and alert.

> **Authorization note:** Only test systems you own or have explicit written permission to test. Everything
> here runs locally in Docker against a container you own — no external targets, no authorization needed.
> The moment you point this loop at a real fleet: reconcile only hosts you are authorized to manage, and
> never auto-revert a production change without a change-management policy that says which classes of drift
> may be auto-healed and which must alert-and-hold for a human.

## Scenario

Meridian Financial hardened its Ubuntu fleet to a CIS baseline (Module 03), pushed it as an Ansible
playbook (Module 06), and scored it compliant (Module 07). That was a *project*. Now it has to become a
*program*: the hosts that passed in January must *stay* passing in March, when nobody is watching. A package
update has already silently flipped a sysctl on one host; an on-call engineer re-opened root SSH at 2 a.m.
to debug an outage and forgot to revert it; somebody's deploy left a world-writable file. None of these is
an attack — all of them are drift, and all of them are invisible until something looks. You own the
steady-state loop: declare the baseline, detect drift on a schedule, report *what* changed against *which*
control, reconcile back to baseline, and alert on the delta so the re-opened root login is closed within an
hour, not found ten weeks later in an audit.

The rhythm: **declare (baseline as code) → the world drifts it → detect (scheduled diff) → report the
control-named delta → reconcile (re-converge) → alert (what changed, when) → repeat forever.**

## Do

Build the steady-state loop on the already-hardened host, prove it catches and reconciles real drift, and
make it report *what* changed — not just a score.

### Part 1: Declare the baseline and confirm zero drift at t=0
1. [ ] **Bring it up and converge.** `make up`, then `make baseline`. Open the declared baseline (the
   Module-06-style playbook under `data/`) and note the five controls it asserts (root SSH, password
   complexity, auditd, umask, sysctl). Confirm a `--check --diff` run reports **nothing would change** —
   observed == declared, `t=0`, the gap is zero. *Why is a playbook that reports zero pending changes the
   definition of "no drift"?*
2. [ ] **Establish git as the source of truth.** Confirm the declared baseline lives in the repo, not as an
   editable copy on the target. In your write-up, state the rule you'll enforce for the rest of the lab: a
   change to the *baseline* is a reviewed commit; any change *on the host* that diverges from the committed
   baseline is **drift by definition** and will be reconciled. (This is the judgment the whole loop rests
   on — re-baseline only over *approved* changes, the Module-11 lesson.)

### Part 2: Let it drift — three realistic ways
3. [ ] **Inject drift the way it really happens.** `make drift` injects three: (1) a simulated package
   post-install that flips `net.ipv4.conf.all.rp_filter` back to `0` (the "`apt upgrade` changed a default"
   class), (2) an operator who set `PermitRootLogin yes` in `sshd_config` (the "2 a.m. debug, never
   reverted" class), and (3) a dropped world-writable file (the "deploy loosened a permission" class). Read
   `data/drift.sh`; for each, note which control it violates and how it would look to a user (the host runs
   fine — that's *why* drift is invisible).

### Part 3: Detect and DIFF — name what changed, against which control
4. [ ] **Detect, and demand a control-named delta — not a score.** `make detect` runs the detector. The
   non-negotiable here: the output must say *what* changed and *which control*, e.g.
   `sshd_config:PermitRootLogin no→yes (CIS-5.2.10)`, `net.ipv4.conf.all.rp_filter 1→0 (CIS-3.3.7)`, and the
   world-writable file with its path. Build the detector on the native diff mechanism — `ansible-playbook
   --check --diff` (a pending change *is* drift, shown line-level), with `oscap` and/or osquery as the
   cross-check that re-evaluates against the standard profile and emits per-rule IDs. **Contrast it with a
   score:** also capture the compliance *score* (Module 07 style) and write one line on why "94→92" is
   useless operationally where the named delta is actionable. *A smoke detector that beeps vs. a panel that
   says which room is on fire.*
5. [ ] **Prove the diff is the *delta*, not the full state.** Re-run `make detect` against a *clean* host
   (reconcile first, or a fresh `make baseline`) and confirm it reports **no drift** — the detector reports
   *changes*, so a clean host is silent. A detector that always prints the full config is noise; one that
   prints only the delta is signal.

### Part 4: Reconcile — pull it back to declared
6. [ ] **Re-converge and prove steady-state.** `make reconcile` re-applies the baseline so observed
   converges back to declared. Confirm: the sysctl is `1` again, `PermitRootLogin no` again, the
   world-writable file is gone (or its mode corrected), and a follow-up `make detect` reports **zero drift**.
   This is the steady-state proof — the gap that opened in Part 2 is closed.
7. [ ] **Make the reconcile-vs-alert decision explicit (the real judgment).** Not everything should
   auto-heal silently. In your write-up, classify each of the three drifts: *auto-reconcile-and-alert* (the
   flipped sysctl, the re-opened root login — mechanical, clearly-wrong, re-converge and log) vs.
   *alert-and-hold-for-human* (a higher-risk or ambiguous class you'd choose). State the failure mode of
   auto-healing *everything* silently: if a nightly package job keeps re-flipping the sysctl and your loop
   keeps quietly fixing it, you've **masked the recurring cause** — the alert exists so a human sees "this
   drifted three nights running" and goes fixes the upstream job.

### Part 5: Alert and schedule — make it a loop, not a scan
8. [ ] **Wire the alert on the delta.** `make loop` runs the full beat: detect → diff → (reconcile) → alert.
   The alert must carry the *delta* — which control, before→after, timestamp — not just "drift detected."
   Confirm: inject drift, run the loop, and a structured drift-event line/record is produced naming each
   changed control. Confirm the inverse too: a clean host produces **no alert** (no false alarms).
9. [ ] **Schedule it.** Wire the loop to run on a schedule (cron in the container, or the GitHub Actions
   cron in *Automate & own it*). A drift control that you have to remember to run by hand is not a drift
   control — the schedule and the alert are what make it *steady-state*. Prove it: introduce drift, let the
   scheduled run catch it, and read the resulting drift-event log.

## Success criteria — you're done when
- [ ] At `t=0` the declared baseline reports **zero drift** (`--check --diff` shows nothing would change),
      and you stated the git-is-source-of-truth rule (approved change = commit; host edit = drift).
- [ ] After `make drift`, your detector reports a **control-named delta for all three** drifts —
      *what* changed, before→after, and *which control* — and you contrasted it against the unactionable
      score.
- [ ] The detector reports the **delta only** (a clean host is silent; it doesn't dump full state).
- [ ] `make reconcile` re-converges the host so a follow-up detect shows **zero drift** — steady-state
      restored — and you classified each drift as auto-reconcile-and-alert vs. alert-and-hold, naming the
      silent-auto-heal-hides-the-cause failure mode.
- [ ] The loop **alerts on the delta** (control + before→after + timestamp), produces **no alert on a clean
      host**, and runs on a **schedule** — proven by a scheduled run catching an injected drift.

## Deliverables
Commit to your portfolio repo:
- `drift-loop/` — the running loop: the declared baseline (the playbook), the detector that produces the
  control-named diff, the reconcile step, the alert formatter, and the schedule wiring (cron / Actions).
- `drift-policy.md` — the **reconcile-vs-alert policy**: per drift class, auto-reconcile-and-alert vs.
  alert-and-hold-for-human, *with the reasoning*; plus the git-is-source-of-truth rule (an approved change
  is a reviewed baseline commit, not a host edit).
- `drift-events.md` — the **proof**: the `t=0` zero-drift capture; the post-`make drift` control-named delta
  for all three drifts (alongside the contrasting bare score, to show why the delta is the one that's
  actionable); the post-reconcile zero-drift capture; and one scheduled-run drift-event record showing the
  loop catching drift unattended.

Do **not** commit: the target's generated host keys, the raw `oscap` results XML / full ansible run logs
beyond the curated delta lines, or the lab's seeded baseline data (it lives in the lab repo, not yours).

## Automate & own it
**Required — this is the detect-diff-reconcile-alert loop turned into a scheduled control you actually
trust.** A drift loop you have to run by hand is a scan, not a control. Build the loop into a small wrapper,
`drift-loop.sh`, that a model drafts and **you review every line of**:
1. **Detect & diff:** run `ansible-playbook --check --diff` (and/or `oscap` re-scan) and parse the output
   into a **control-named delta** — for each drifted item: the control/rule ID, the before→after value, the
   path. (Not a score.)
2. **Reconcile:** for the auto-reconcile classes from your policy, re-apply the baseline; for alert-and-hold
   classes, do *not* auto-fix.
3. **Alert:** emit a structured drift-event record (control, before→after, timestamp, action taken) on every
   delta, and **exit non-zero when drift was found** so a CI/cron job can alarm.

Then wire it as a **GitHub Actions scheduled workflow** (cron: daily) that spins up the target container,
runs `drift-loop.sh`, and fails the job — surfacing the alert — when drift is detected. **Review every
line for the two things the model gets wrong:** (a) the loop must **never auto-heal silently** — every
delta must produce the alert *before* (or alongside) the reconcile, or a recurring cause hides forever; and
(b) the detector must **fail closed** — if the check itself errored (the controller couldn't reach the
target, the parse broke), that must count as a *failure to verify*, never a silent "no drift." The most
dangerous bug here is a loop that reports "clean" because it *couldn't actually look*. (AI drafts; you prove
the alert always fires and the signal is honest, and you own the reconcile-vs-alert policy.)

## AI acceleration
Ask a model to draft the diff parser (turn raw `--check --diff` / `oscap` XML into a clean control-named
delta table), the osquery scheduled-pack queries, the alert formatter, and the Actions cron — that's real
leverage on the tedium. Then refuse its default design. Asked to "build a drift loop," a model writes a cron
that re-runs the enforcement playbook and reports "fixed" — a loop that **auto-heals everything silently**,
which is exactly the failure mode that hides a recurring root cause and quietly papers over a
security-relevant change night after night. The judgment it cannot make for you: the **reconcile-vs-alert
decision per control class**, and **whether a change is drift or an approved baseline update** — it doesn't
know your change-management context, so it can't tell that last night's `sshd_config` edit was an authorized
2 a.m. fix that should become a *commit*, not be silently reverted. Make it draft the parser, queries, and
format; **you** decide what auto-reconciles vs. alerts, confirm the alert *always* fires on a delta (nothing
heals invisibly), and own that the declared baseline in git is the source of truth. Then ask it: "what could
make this loop report clean when it isn't?" — and verify each answer (a broken check, an unreachable target,
a parse that swallowed errors) fails closed against an actual injected drift, not the model's claim.

## Connects forward
This is the steady-state engine the rest of the track and the capstone assume. The baseline you keep
enforced is the **Module 06** playbook; the score you contrast the delta against is **Module 07**'s
compliance scoring — this module is "now make it a *loop* that runs while you sleep and tells you *what*
changed." It's the same detect→diff→reconcile shape as **Module 11**'s file-integrity monitoring one layer
over (config drift vs. file drift; both rest on a *trustworthy reference*). The control-named delta is what
the capstone's "drift detection is automated/scheduled and reports *what* changed" Exemplary bar is asking
for. And the very next module — **Module 13 (Fleet Migration)** — is where you *roll this baseline across an
existing fleet*; once it's rolled, this loop is what keeps every one of those hosts from drifting back.

## Marketable proof
> "I build the steady-state loop that keeps a hardened host hardened: declare the baseline as code, detect
> drift on a schedule, and — critically — report *what* changed against *which* control (`PermitRootLogin`
> no→yes, CIS-5.2.10), not just a score that dropped two points. The loop reconciles mechanical drift back
> to baseline and alerts on the delta, and I can defend the reconcile-vs-alert policy — why auto-healing
> *everything* silently hides the recurring cause, and why an approved change is a reviewed commit to the
> baseline, never a manual edit on the host."

## Stretch
- **Drift over time, not just a point check.** Log every scheduled run's delta to a time-series (or just an
  append-only log) and produce a "drift rate" per control — which controls drift most, and which host. The
  control that re-drifts three nights running is your real bug (a misbehaving package job), and surfacing
  *that* is the whole point of alert-over-silent-heal.
- **Reconcile is the dangerous half — prove a bad reconcile can't make it worse.** Plant a "reconcile"
  action that's subtly wrong (it fixes the symptom but disables auditd in the process) and show your loop
  catches that the *reconcile itself* introduced drift on the next detect — a reconcile you don't re-verify
  is a new failure mode.
- **Cross-tool corroboration.** Run `ansible --check --diff`, `oscap`, and an osquery pack against the same
  drifted host and reconcile their three views into one delta — where they agree, where one sees a drift the
  others miss, and which tool is authoritative for which control class.

---

## Lab-env spec (to be built & validated at promotion)

*This module has no `plaintext-labs` directory yet; build it at promotion under
`plaintext-labs/endpoint-hardening/12-config-drift/` and run `make up`/`make demo` green on a Linux runner
before marking the module done. Reuse Module 06's Ansible-controller + target shape so it runs with zero
cloud cost. It must contain:*

- **`docker-compose.yml`** — an **Ansible controller** container and an **Ubuntu target** container on a
  bridge network (the Module-06 shape). The target starts hardened: `make up` converges the five-control
  baseline so the host is at `t=0` (zero drift) before anything else runs.
- **The declared baseline (`data/playbook.yml`)** — the Module-06 five-control hardening playbook (root SSH,
  password complexity, auditd, umask, sysctl), each task verifying its control, fully idempotent. This is
  the *declared state*, treated as the source of truth (in the repo, not editable on the target).
- **Drift injection (`data/drift.sh`, `make drift`)** — injects three realistic drifts: (1) a simulated
  package post-install hook that flips `net.ipv4.conf.all.rp_filter` to `0`; (2) `PermitRootLogin yes` in
  `sshd_config` (the operator-at-2am class); (3) a dropped world-writable file. Idempotent and re-runnable;
  a matching `make undo-drift`/`reset` returns to the clean baseline.
- **The detector + control-named diff (`data/drift-loop.sh`, `make detect`)** — runs `ansible-playbook
  --check --diff` against the baseline and parses output into a **control-named delta** (control/rule ID,
  before→after, path) — *not* a bare score. Cross-checks with `oscap` (a CIS/STIG SCAP profile, per-rule
  pass/fail with rule IDs) and/or osquery scheduled-pack queries for observed state. Reports the **delta
  only** (clean host → silent). **Fails closed**: a controller-can't-reach-target or parse error counts as
  failure-to-verify, never "no drift."
- **Reconcile (`make reconcile`)** — re-applies the baseline (for the auto-reconcile classes) so observed
  re-converges to declared; a follow-up detect must report zero drift. Idempotent.
- **The alert + schedule (`make loop`, cron)** — `make loop` runs detect → diff → (reconcile) → alert,
  emitting a structured drift-event record (control, before→after, timestamp, action) on every delta and
  *no* record on a clean host; exits non-zero on drift. A container cron (or the Actions workflow in
  *Automate & own it*) runs it on a schedule.
- **`Makefile`** — `up` / `baseline` / `drift` / `detect` / `reconcile` / `loop` / `demo` / `shell` /
  `reset` / `down`. `make demo` = baseline (zero drift) → drift → detect (named delta for all three) →
  reconcile → detect (zero drift) → loop (alert fired), the full steady-state walkthrough.
- **CI note:** the core loop is **CI-runnable end-to-end** (baseline → drift → detect-named-delta →
  reconcile → zero-drift is fully scripted and deterministic), so add a **`.ci-demo`** marker once `make up
  && make demo && make down` is green on a Linux runner — this is a reference lab whose demo proves the loop
  works on a clean runner (unlike Module 06's learner-exercise gate). The learner's *own* extension
  (their policy, their alert wiring) is on top of a demo that already passes.
