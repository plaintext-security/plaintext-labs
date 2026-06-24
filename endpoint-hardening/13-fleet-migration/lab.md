# Lab 13 — Rolling a Hardening Baseline Across a Fleet: Ring by Ring, With No Outage

*Type 12 · Migration / Brownfield. [← Back to the module concept](README.md)*

**Type 12 · Migration / Brownfield.** You take a small fleet of already-running, in-service hosts — each
serving a live app — and roll the Module-06 hardening baseline across it *incrementally without an outage*:
define **rings** (test → canary → fleet), apply the baseline one ring at a time, prove with a
**service-health check before and after each ring** that every host is now hardened *and* still serving,
carve out a **defended exception** for the legacy-app host the benchmark would break, keep a **per-ring
rollback** you actually run, and only at the end declare the fleet hardened. The deliverable is the *rollout
runbook + ring plan + the health-check proof of no-outage + the per-ring rollback* — not a writeup. No
grader; you verify your own work against the observable success criteria below. (Honor system: the committed
runbook, the health-check proofs, and the rolling playbook are the proof.)

## Setup

> **Lab env to be built & validated at promotion.** This is the endpoint track's first Type 12 and has
> **no `plaintext-labs` directory built yet** — the **Lab-env spec** at the end of this file is the build
> contract. It reuses Module 06's Ansible-controller shape and adds a small *running fleet* of target
> containers (each serving an HTTP health endpoint) plus the rings, the health-check harness, and a legacy
> host that breaks under the full baseline — all in Docker, with **zero cloud credentials and zero cost**.
> Until `make up`/`make demo` has actually been run green on a Linux runner, treat the first run as the
> validation pass. Every command below is real and runs on a laptop with Docker installed.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/endpoint-hardening/13-fleet-migration
make up               # bring up the fleet: ~6 already-running target hosts, each serving an app + health endpoint
make health           # baseline service-health: every host serves its app (200) BEFORE any hardening
make roll RING=test   # apply the baseline to the test ring only; health-check before/after
make roll RING=canary # apply to the canary (small production slice); health-check before/after
make roll RING=fleet  # apply to the rest, in batches (serial + max_fail_percentage), health-checked per batch
make rollback RING=canary  # re-converge a ring to the previous baseline (the per-ring rollback)
make health           # prove every host is hardened AND still serving
make shell            # drop into the controller to run ansible by hand
make down
```

`make up` stands up a **fleet that is already in service**: ~6 Ubuntu target hosts on a bridge network,
*each running a small app with an HTTP health endpoint* (the host is doing a job; it isn't an empty box).
One of them is in a **`legacy-app` group** that will *break* under the full baseline (its app needs a
setting the benchmark tightens) — the host that forces the exception decision. `make roll RING=<ring>`
applies the Module-06 baseline to one ring at a time; `make health` is the service-health check that proves
no-outage. The gap between "the Ansible run went green" and "the app is still up" is the whole lab.

> **Authorization note:** Only test systems you own or have explicit written permission to test. Everything
> here runs locally in Docker against containers you own — no external targets, no authorization needed. The
> moment you point this rhythm at a real fleet: harden only hosts you are authorized to manage, never roll a
> control to the whole fleet before it has survived a test ring and a canary with a tested rollback, and
> never declare a host "hardened" without proving its application still serves.

## Scenario

The organization has 800 Ubuntu hosts that have run in production for years — app servers, internal
tools, a couple of legacy boxes nobody wants to touch. Audit says they must all meet the CIS baseline you
wrote in Module 06. The one rule from the VP of Engineering: **do not break production.** You cannot pick a
Saturday and `ansible-playbook` the whole fleet — a big-bang rollout changes every host at once, so when a
control breaks something (a tightened cipher kills the legacy app, a sysctl drops the database's long-lived
connections) you've broken it *everywhere*, can't tell which control did it, and can't roll back one host to
bisect. You've seen what big-bang looks like when the change is wrong: CrowdStrike, July 2024, one update to
the whole Windows fleet, ~8.5M machines down in an hour. So you roll it the staged way: test ring → canary
→ fleet, prove service health before and after every ring, carve out a defended exception for the legacy
box, and keep a rollback at every step.

The rhythm of each ring: **health-check before (serving) → apply the baseline → health-check after
(hardened AND still serving) → keep the rollback → next ring.**

## Do

Roll the baseline across the running fleet ring by ring, proving no host went down and carving out the one
host the benchmark would break.

### Part 1: Baseline the fleet — it's running, and you must prove it stays running
1. [ ] **Bring it up and prove the starting state.** `make up`, then `make health`. Confirm **every host
   serves its app** (a 200 from its health endpoint) — this is the *before* you must preserve. Note in your
   runbook: these hosts are *in service*; the success bar is not "compliant," it's "compliant **and** still
   serving." Record the per-host baseline health.
2. [ ] **Inventory and ring the fleet.** Group the hosts into **rings** in your runbook: a **test ring** (1–2
   non-critical hosts — the staging box, the one you can lose), a **canary** (1–2 real production hosts, a
   small slice), and the **fleet** (the rest). Write the order **least-risky-first** with one line of *why*
   each host is where it is (blast radius, dependencies, whether it's the legacy box). Identify the
   **`legacy-app` host** now — it's the one you predict will break.
3. [ ] **Name the big-bang trap before you avoid it** (predict, then confirm). In your runbook, write what
   would happen if you `make roll RING=fleet`-everything at once: every host changes simultaneously, a single
   bad control (the legacy app's cipher) breaks production with no way to bisect which control did it and no
   per-host rollback — a fleet-wide outage debugged live. **You will not do this.** *(Stretch step 1 below
   lets you actually watch it fail.)*

### Part 2: Test ring — the first place a broken control surfaces
4. [ ] **Roll the test ring, health-checked before and after.** Capture the *before* health for the test-ring
   hosts (serving), then `make roll RING=test`. Then capture the *after* and assert **both**: (a) the host is
   now **hardened** (the baseline applied — re-scan/`--check` shows compliant) **and** (b) it is **still
   serving** (health endpoint still 200 — *no outage*). *Compliant alone is not done* — a host that passes
   the benchmark but stopped serving is a **failed** roll, not a success. Confirm the rest of the fleet is
   **untouched** (still serving on the old config) — the strangler-fig guarantee: one ring moves, nothing
   else does.

### Part 3: Hit the exception — the legacy host the benchmark breaks
5. [ ] **Roll the canary and watch the legacy host break.** `make roll RING=canary` against a canary that
   *includes the `legacy-app` host*. The health check **after** will fail for that host: it's now compliant
   but its app is **down** (a control the baseline applied broke it). This is the predicted failure, and it's
   the whole point — *a control that's harmless on an empty box is catastrophic on a running one.* Read which
   control broke it.
6. [ ] **Decide the exception — and DEFEND it (the real judgment).** You have three options; pick and justify
   in the runbook: (i) break the app (wrong — you took down production), (ii) silently skip the host (wrong —
   a lie in your compliance report), or (iii) a **defended, documented exception**: give the `legacy-app`
   host a *relaxed profile* for the one breaking control, with the **reason and a compensating control**
   recorded (e.g. "`legacy-app` retains setting X because vendor app Y requires it; compensating control:
   network-isolated, scheduled for replacement Q3"). Implement the exception (a group_vars override),
   re-roll the canary, and prove the after-state: the legacy host is **hardened to its relaxed profile AND
   serving**, every other canary host is hardened to the full baseline AND serving. This is "accept the risk
   with justification" (Module 03/07) at fleet scale.

### Part 4: Roll the fleet in batches — and halt on failure
7. [ ] **Capture and run the per-ring rollback.** Before the fleet ring, write the canary's one-line rollback
   in the runbook, then **run it**: `make rollback RING=canary` re-converges the canary to the *previous*
   baseline. Confirm those hosts serve the old way again within seconds (you only changed one ring, so
   backing out is cheap), then re-roll to restore the migrated state. A rollback you wrote but never ran is
   not a rollback.
8. [ ] **Roll the fleet in batches, never all at once.** `make roll RING=fleet` applies to the rest using
   Ansible `serial` (process N hosts/% at a time) with `max_fail_percentage` set so the rollout **halts** the
   moment a batch's failures cross the threshold — a bad control stops the roll instead of completing it.
   Health-check **each batch** before and after (hardened AND serving). Prove the halt works: confirm that if
   a batch failed health, the rollout would stop with the *rest of the fleet untouched* (not all-down).

### Part 5: Declare done — only when every host is across and healthy
9. [ ] **Final fleet-wide proof.** With every ring across, run `make health` over **all** hosts and assert
   the end state: every host is **hardened** (full baseline, or its defended relaxed profile for the legacy
   class) **and still serving** (200). The un-hardened surface is zero, and **no host had an outage** at any
   point. Save this final all-hosts before/after table — it's the deliverable's core proof.

## Success criteria — you're done when
- [ ] You showed the starting state: **every host was in service (serving 200)** before any hardening, and
      you ringed the fleet test → canary → fleet, least-risky-first, with the *why* per host and the
      `legacy-app` host identified.
- [ ] You named the **big-bang trap** in your runbook (every host changes at once; no bisect; no per-host
      rollback; a fleet-wide outage) — the failure your ring rhythm avoids.
- [ ] **Every ring** was rolled with a **service-health check before and after**, asserting both: the host
      is now **hardened** *and* **still serving** — *compliant ≠ done*; a host that passed the benchmark but
      stopped serving is a failed roll.
- [ ] You hit the **legacy-app break**, and resolved it with a **defended, documented exception** (relaxed
      profile for the one breaking control + reason + compensating control) — not a silent skip and not a
      broken app.
- [ ] You have a **per-ring rollback** you *ran* at least once and proved restores a ring's hosts to serving
      in seconds, and the fleet roll used **batches** (`serial` + `max_fail_percentage`) that would **halt**
      on a failed batch rather than complete.
- [ ] After the **last** batch, you proved fleet-wide: every host is hardened (or on its defended exception)
      **and** still serving — the un-hardened surface is zero, **no host had an outage** — captured as a
      before/after table.

## Deliverables
Commit to your portfolio repo:
- `rollout-runbook.md` — the staged runbook: the ring plan and *why that order* (blast radius, dependencies,
  the legacy host), the named big-bang trap you avoided, the batch sizes / `max_fail_percentage` for the
  fleet ring, and per ring the before/after health result.
- `ring-plan.md` — the **ring assignment**: each host → its ring, with the one-line reason; the canary
  fraction and why; the halt threshold and what happens when a batch fails.
- `exception-adr.md` — the **defended exception** for the `legacy-app` host: the option that breaks the app
  (full baseline), the decision (relaxed profile for control X), the *reason*, and the **compensating
  control** + remediation timeline. The "accept-with-justification" decision, written as a small ADR.
- `no-outage-proof.md` — the **health-check proof**: per ring, the *before* capture (host serving, 200) and
  the *after* capture (host hardened — compliant — **and** still serving, 200), the one rollback capture
  proving a ring came back, and the final all-hosts post-fleet table (every host hardened/exception AND
  serving).
- the rolling playbook itself (`serial` + `max_fail_percentage` + pre/post health hooks).

Do **not** commit: the target hosts' generated keys, raw full Ansible run logs beyond the curated
before/after lines, or the lab's seeded app/fleet data (it lives in the lab repo, not yours).

## Automate & own it
**Required — this is the service-health check turned into a reusable rollout gate.** A rollout you can't
*prove* didn't break anything is a rollout you don't actually trust. Build the health check into a harness,
`fleet-health.sh <ring>`, that a model drafts and **you review every line of**, asserting per host and
exiting non-zero on any failure:
1. **Serving (no outage):** each host's app health endpoint returns **200**.
2. **Hardened:** the host is at its expected profile (full baseline, or the legacy host's relaxed profile) —
   a `--check`/re-scan shows compliant *for the profile that host is supposed to have*.

Wire it as the **gate inside the rolling playbook** (pre/post-task per batch, the Ansible rolling-upgrade
pattern: health-check → apply → health-check → next batch) so `make roll` *halts* if any batch fails the
after-check, and as a `make health` target that runs it across **all** hosts. **Review every line for the
two things the model gets wrong:** (a) it must assert **both** serving *and* hardened — a harness that only
checks the CIS score (and not that the app is up) is the exact compliant-but-down failure mode this lab
exists to teach; and (b) it must **fail closed** — a health check that *errored* (the endpoint timed out, the
controller couldn't reach the host) must count as a **failure**, never a silent pass, or you'll roll the
next ring on top of an outage you didn't notice. The most dangerous bug here is a harness that goes green
because it merely *couldn't reach* the app and read that as healthy. (AI drafts; you prove the signal is
honest and you own the gate.)

## AI acceleration
Ask a model to draft the ring plan, the `serial`/`max_fail_percentage` rolling playbook, and the
`fleet-health.sh` harness — then refuse to trust its plan. The model's default is **big-bang**: ask it to
"harden the fleet" and it hands you one run for every host, because that's the simplest thing to express and
it has no idea which of your hosts is the database serving live traffic. The judgment it cannot do for you is
**sequencing by blast radius** (test-ring vs. canary vs. fleet, the canary fraction, which host needs the
exception) and **the service-health check** — asked to "confirm the rollout worked," a model checks the
Ansible run went green and the CIS score rose and calls it done, **missing that the app is now down**
(compliant ≠ working). Make it draft the plan, the playbook, and the harness; **you** decide the ring order
and canary size, confirm every ring has a *tested* rollback, own the *defended* exception for the legacy
host, and verify the after-state proves *hardened **and** still serving* before any control reaches the
fleet. Then ask it: "what would make this rollout report success while production is down?" — and verify
each answer (a harness that only checks compliance, a health check that passes on a timeout) fails closed
against an actual broken host, not the model's claim.

## Connects forward
This is the brownfield reality that makes the whole track real. The baseline you roll is the **Module 06**
playbook; the compliance you assert per host is **Module 07**'s scoring — this module is "now apply it to
hosts that are *already running and can't go down*." The moment the fleet is hardened, **Module 12 (Drift)**
is what keeps it that way: the detect→reconcile loop runs across the very fleet you just rolled, catching
the hosts that drift back. The defended exception is a small **Decision/ADR** (the construct the track uses
implicitly for CIS L1-vs-L2 and accept-with-justification), now produced as an artifact. And the staged
rollout + per-ring rollback discipline is exactly what the **capstone** assumes when it asks you to bring a
fleet to a baseline and *prove* nothing broke.

## Marketable proof
> "I roll a hardening baseline across a fleet of already-running, in-service hosts without downtime —
> staged, ring by ring: test ring → canary → fleet in batches with `serial`/`max_fail_percentage` that
> *halts* on a bad batch. I prove every ring with a service-health check before and after, because
> *compliant is not working* — a host that passes the benchmark but stopped serving is a failed rollout. I
> carry a tested per-ring rollback, I produce a **defended exception** (relaxed profile + compensating
> control) for the legacy app the benchmark would break instead of skipping it silently, and I can explain
> why big-bang rollouts cause global outages — CrowdStrike, ~8.5M machines, one update — and why blast
> radius is a choice."

## Stretch
- **Actually watch the big-bang fail.** Add a `make roll-bigbang` that applies the full baseline to every
  host at once (legacy box included) and run `make health` after: production is down, you can't tell which
  control did it, there's no per-host rollback. Then do it the staged way and contrast — the fastest way to
  *feel* why rings exist.
- **Automated canary analysis.** Don't eyeball the canary — compute it. Keep a control group on the old
  baseline, compare the canary's health/error metrics against the control (Google SRE style), and *gate the
  fleet roll on a statistical "the canary is no worse than control"* signal, not a human glance.
- **Snapshot-based rollback for the irreversible control.** Some controls aren't cleanly reversible by
  re-converging. For one such control, take a host snapshot before the ring and make `make rollback` restore
  the snapshot instead of re-running the playbook — and prove the host serves again — so even an irreversible
  change has a tested per-ring rollback.

---

## Lab-env spec (to be built & validated at promotion)

*This module has no `plaintext-labs` directory yet; build it at promotion under
`plaintext-labs/endpoint-hardening/13-fleet-migration/` and run `make up`/`make demo` green on a Linux
runner before marking the module done. Reuse Module 06's Ansible-controller shape so it runs with zero cloud
cost. It must contain:*

- **`docker-compose.yml`** — an **Ansible controller** plus a small **fleet of ~6 Ubuntu target hosts** on a
  bridge network, *each running a tiny app with an HTTP health endpoint* (so the host is in service, not an
  empty box) — `whoami`/a minimal HTTP service is fine. One target is in a **`legacy-app` group** configured
  so the **full baseline breaks its app** (its service depends on a setting one CIS control tightens — e.g.
  a permission/`umask`/cipher the baseline changes), forcing the exception decision. All hosts start
  *unhardened but serving*.
- **The baseline (`data/playbook.yml`) + inventory with ring groups** — the Module-06 five-control hardening
  playbook, plus an inventory grouping hosts into `test`, `canary`, `fleet`, and `legacy-app`, with
  `group_vars` so the `legacy-app` group can take a **relaxed profile** for the breaking control (the
  exception mechanism). Idempotent.
- **The rolling rollout (`make roll RING=<ring>`)** — applies the baseline to the named ring. For
  `RING=fleet`, uses Ansible **`serial`** (batch size / ramp) and **`max_fail_percentage`** so the rollout
  **halts** when a batch's failures cross the threshold, with pre-/post-task **health hooks** (the
  rolling-upgrade pattern: health-check → apply → health-check). `make rollback RING=<ring>` re-converges
  that ring to the previous (un-hardened or prior) state — idempotent, re-runnable, fast.
- **The service-health harness (`fleet-health.sh`, `make health`)** — the success signal: per host, asserts
  **(a) serving** (app health endpoint → 200) **and (b) hardened to its expected profile** (full baseline,
  or the legacy host's relaxed profile — `--check`/re-scan compliant *for that host's profile*). **Fails
  closed**: a timeout/unreachable host counts as failure, never a silent pass. It should pass for rolled
  rings, show the legacy host *broken* under the full baseline (before the exception) and *healthy* after the
  exception, and pass for all hosts at the end.
- **`Makefile`** — `up` / `health` / `roll RING=…` / `rollback RING=…` / `demo` / `shell` / `reset` /
  `down`. `make demo` = health (all serving) → roll test (hardened+serving) → roll canary incl. legacy
  (legacy breaks) → apply exception (legacy healthy on relaxed profile) → rollback canary + re-roll → roll
  fleet in batches → final health (all hardened/exception AND serving), the full staged walkthrough.
- **CI note:** the staged path is **CI-runnable end-to-end** (health → roll test → roll canary → exception →
  roll fleet → final health is fully scripted and deterministic, including the legacy break-then-fix), so add
  a **`.ci-demo`** marker once `make up && make demo && make down` is green on a Linux runner — a reference
  lab whose demo proves the staged rollout (and the exception) works on a clean runner. The learner's *own*
  work (their ring plan, their exception ADR, their gate) builds on a demo that already passes.
