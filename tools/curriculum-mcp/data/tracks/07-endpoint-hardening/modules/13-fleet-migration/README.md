# Module 13 — Rolling a Hardening Baseline Across a Fleet

*Type 12 · Migration / Brownfield — take a fleet of already-running, in-service hosts and roll a hardening baseline across it *incrementally without breaking production*: test ring → canary → fleet, exception carve-outs for the legacy app the benchmark would break, a service-health check before/after each ring, and a rollback at every step. The deliverable is the rollout runbook + ring plan + the proof (health checks) that no host went down + the per-ring rollback — not an essay. (Secondary: Decision/ADR — the exception carve-out is a defended "accept-with-justification" decision.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Endpoint & Host Hardening** — *hardening one host you just provisioned is a tutorial; hardening eight hundred hosts that are already in service, already serving traffic, and can't take downtime is the actual job — and the way you break production is to apply the baseline to all of them at once.*

<!-- module-meta -->
**Difficulty:** Intermediate–Advanced &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Module 06 — Configuration Management](../06-configuration-management/README.md) (the baseline-as-code you roll), [Module 12 — Configuration & Posture Drift](../12-config-drift/README.md) (what keeps it enforced after) &nbsp;·&nbsp; helpful: [Module 07 — Compliance Scoring](../07-compliance-auditing/README.md)
{ .module-meta }

## Why this matters

Every hardening lab in this track — Modules 02, 03, 06 — starts from a host you just provisioned. A clean box, no users, no running services, nothing to break. You apply the CIS baseline, re-scan, and it's compliant on the first try because there was never any production on it. That is **greenfield**, and almost no real hardening project starts there. The project you actually walk into is **brownfield**: a fleet of hundreds of hosts that have been *in service for years*, running applications the business depends on, serving traffic right now, that you are told to bring up to a hardening baseline — and the one rule is **you cannot break production.** A CIS control that's harmless on an empty box can be catastrophic on a running one: disabling a "weak" cipher breaks a legacy app that only speaks it; tightening `umask` breaks a service that relied on group-writable files; enforcing a sysctl drops the long-lived connections a database cluster depends on. Hardening *is* change, and change to a running fleet is how outages happen.

The naive move is the one almost every team is first tempted to make, and it is the disaster this module exists to prevent: push the hardening baseline to the entire fleet at once. It feels efficient — one Ansible run, all hosts, done by lunch. It is the **big-bang rollout**, and it fails for a reason that has nothing to do with whether the baseline is *correct*: it changes *every host simultaneously*, so when a control breaks something (and on an un-inventoried brownfield estate, something always breaks), you've broken it *everywhere at once*, you can't tell which of the dozens of controls did it, and you can't roll back one host to bisect — you're debugging a fleet-wide outage live. This is not hypothetical. On 19 July 2024, **CrowdStrike pushed a single content update to its entire Windows fleet at once**; a malformed channel file caused an out-of-bounds read and blue-screened ~8.5 million machines globally within about an hour — hospitals, airlines, banks. The defect was real, but the *blast radius* was a choice: a change validated and shipped to everything simultaneously, with no staged ring to catch it on a handful of machines first. The lesson the whole industry re-learned that day is the lesson of this module — **it's not whether your change is good; it's how many machines you bet on being right.**

The correct path is **test ring → canary → fleet**, the staged rollout every team that has done this at scale runs. You do not push to everything. You apply the baseline to a small **test ring** first (a handful of representative hosts, off the critical path), prove with a *service-health check* that nothing the host serves went down, then to a slightly larger **canary** (real production hosts, but a tiny fraction — if a control breaks here it's a small, recoverable blast radius), prove health again, and only then to the **fleet**, in batches, health-checked at each batch, with a **rollback ready at every step**. Two things make it safe that the big-bang has neither: a **service-health check before and after each ring** (the host is still hardened *and* still doing its job — a host that's compliant but down is a failed rollout), and an **exception carve-out** for the host class the benchmark would genuinely break (the legacy app that needs the weak cipher) — a *defended, documented* exception, not a silent skip. The un-hardened surface shrinks toward zero one provable ring at a time, and no control reaches the whole fleet until it's survived contact with a small, recoverable slice.

## Objective

Take a fleet of already-running, in-service hosts and roll the Module-06 hardening baseline across it
*without an outage*. Define the **rings** (test → canary → fleet) and the order; apply the baseline to one
ring at a time; **prove with a service-health check before and after each ring** that every host is now
hardened *and* still serving (no outage); carve out a **defended exception** for the legacy-app host class
the baseline would break (document *why*, not skip silently); keep a **per-ring rollback** you have actually
run; and only when every ring is across and proven do you declare the fleet hardened. The deliverable is the
rollout runbook + ring plan + the health-check proof of no-outage + the rollback.

## The core idea

The mental model is the **strangler fig** (Martin Fowler) applied to *hardening a running fleet*: you do
not flip every host to the new baseline in one cutover. You grow the hardened state across the fleet
*incrementally*, one ring at a time, proving each ring is healthy before the next — and the un-hardened
surface shrinks toward zero while the fleet never stops serving. Big-bang is the failure mode the pattern
exists to prevent: applying the baseline to every host at once is a single blast radius with no incremental
rollback and no way to bisect which control broke what, debugged live against the whole business. The
CrowdStrike outage is what big-bang looks like when the change is wrong — and the change is *sometimes*
wrong, which is exactly why you never bet the whole fleet on it.

The mechanism that makes it incremental is **rings: concentric cohorts of hosts ordered by blast radius,
each a gate to the next.** A **ring** is a named set of hosts you treat as one rollout unit. The **test
ring** is a handful of representative-but-non-critical hosts (a staging box, a host you can lose) — the
first place a broken control surfaces, where the blast radius is "nothing important." The **canary** is a
small fraction of *real production* hosts (Google's SRE practice: expose a small slice and keep a control
group on the old state to compare) — large enough to catch problems the test ring's synthetic load missed,
small enough that if a control breaks, the outage is a sliver, not the fleet. The **fleet** is the rest,
rolled in *batches* (never all-at-once even at the end) — Ansible's `serial` keyword and the rolling-upgrade
pattern give you exactly this: process N hosts (or N%) at a time, with `max_fail_percentage` to *halt the
whole rollout* the moment a batch's failure rate crosses a threshold, so a bad control stops the rollout
instead of completing it. The order is **by blast radius, least-risky-first**: a control reaches the fleet
only after it has survived the test ring and the canary, so each ring is a gate the change must pass.

The discipline that makes it safe — and the thing that separates a real rollout from a checkbox one —
reduces to **the service-health check before and after every ring: the host must be both *hardened* and
*still serving*.** A hardening rollout has a seductive false success signal: the Ansible run went green, the
CIS score went up, ship it. But *compliant* is not *working* — a host that passes the benchmark and can no
longer serve its application is a **failed rollout**, not a successful one, because hardening that takes
production down has defeated its own purpose. So at every ring you capture the *before* (the host serves its
app — a real health endpoint returns 200, the service is up, connections work) and the *after* (the host is
now hardened **and** still serves — same health check still passes). Both, or the ring fails and you roll it
back. The rollback is cheap precisely because you only changed one ring: re-converge that ring to the
*previous* baseline (or restore the snapshot) and it's serving again in minutes while you debug *one small
slice*, not a fleet-wide outage. Only when the last batch of the fleet is across and health-checked do you
declare done.

The honest judgment that most distinguishes this from a naive rollout is the **exception carve-out**: some
fraction of the fleet *will* break under the full baseline, and the right answer is not "skip those hosts
silently" nor "break them anyway." Real fleets have a legacy app that only speaks an old TLS cipher the
benchmark disables, or a service that depends on a setting the baseline tightens. The discipline is a
**defended, documented exception** — a host class gets a *relaxed* profile for the specific control that
would break it, with the *reason* recorded ("hosts in `legacy-app` group retain cipher X because vendor app
Y requires it; compensating control: network-isolated, scheduled for replacement Q3") — the "accept the risk
with justification" move from Module 03/07, now applied at fleet scale. This is a small **Decision/ADR**
embedded in the rollout: the option (full baseline) breaks a real thing, so you choose a scoped exception
and *defend it*, rather than either taking down the app or pretending the host is fully hardened when it
isn't. An exception you can point to and justify is hardening; a silent skip is a lie in your compliance
report.

## Learn (~3.5 hrs)

**The pattern — why staged beats big-bang (~1.25 hrs)**
- [Martin Fowler — *Strangler Fig Application*](https://martinfowler.com/bliki/StranglerFigApplication.html) (~15 min) — the canonical essay on incremental replacement: grow the new state around the running system, shift gradually, never cut over in one stroke. Read it for the *why* — gradual change de-risks what a big-bang cannot. The metaphor maps one-to-one onto rolling a baseline ring-by-ring while the fleet keeps serving; it's the mental model the module rests on.
- [Google SRE Workbook — *Canarying Releases* (Ch. 16)](https://sre.google/workbook/canarying-releases/) (~45 min) — the rigorous treatment of *canary*: a partial, time-limited rollout to a small population with a control group, evaluated before you proceed. Read the **population-size**, **metrics**, and **blast-radius** sections — the worked example (a change that fails 20% of requests but only sees 5% of traffic ⇒ ~1% overall) is the quantitative case for why the canary ring exists. This is the discipline behind "prove the slice before you scale."
- [CrowdStrike — *Falcon Content Update Remediation and Guidance Hub* (the July 19 2024 incident)](https://www.crowdstrike.com/falcon-content-update-remediation-and-guidance-hub/) (~20 min) — the anchor: a single content update pushed to the *entire* Windows fleet at once, a malformed channel file, an out-of-bounds read, ~8.5M machines blue-screened globally inside an hour. Read the root-cause and impact summary as the case study in *blast radius as a choice* — the defect was real, but shipping it to everything simultaneously (no staged ring) is what made it a global outage. This is what big-bang looks like when the change is wrong.

**Doing it with the tools — batches, health checks, halting on failure (~1.25 hrs)**
- [Ansible — *Continuous Delivery and Rolling Upgrades*](https://docs.ansible.com/ansible/latest/playbook_guide/guide_rolling_upgrade.html) (~30 min) — the concrete rolling-rollout pattern: `serial` to process the fleet N (or N%) hosts at a time instead of all at once, `max_fail_percentage` to **halt the whole rollout** when a batch's failures cross a threshold, and the pre-/post-task hooks (pull the host out of the load balancer, apply, health-check, return it) that are exactly the per-ring service-health discipline. Read it as the mechanics of "rings and batches" in the tool you already use.
- [Ansible — *Controlling playbook execution: strategies and more* (`serial`)](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_strategies.html) (~20 min) — the reference for `serial` batch sizes (a number, a percentage, or a *ramp* — `[1, 5, 10, "30%"]` to start tiny and grow). The ramp *is* test-ring → canary → fleet expressed in one keyword: bet on one host, then five, then a slice, then the rest. Read the `serial` section.
- [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks) (~15 min) — re-anchor on the baseline you're rolling. Note that benchmarks ship **Level 1** (broadly safe, minimal functionality impact) and **Level 2** (defense-in-depth, *can* break things) profiles — read the page's framing of prescriptive, consensus-based config. The L1-vs-L2 split is itself a blast-radius decision: roll L1 broadly, treat L2 controls as the ones most likely to need the canary and the exception carve-out.

## Key concepts
- **Brownfield is the real hardening job, not the edge case** — hundreds of in-service hosts running production apps that can't take downtime; "apply the CIS baseline" is greenfield advice that doesn't survive contact with a running fleet. Hardening *is* change, and change to a running fleet is how outages happen.
- **Big-bang is the disaster the pattern prevents** — applying the baseline to every host at once is one blast radius, no incremental rollback, no way to bisect which control broke what. CrowdStrike 2024 (~8.5M machines, one update, one hour) is what it looks like when the change is wrong — and the change is *sometimes* wrong.
- **Rings: test → canary → fleet, ordered by blast radius, each a gate to the next** — a control reaches the fleet only after surviving a handful of non-critical hosts, then a small production slice. `serial`/`max_fail_percentage` (and a `serial` ramp) are the tool-level expression: batch the rollout and *halt* when a batch fails.
- **The service-health check before AND after every ring is the real signal** — *compliant ≠ working*; a host that passes the benchmark and can't serve its app is a **failed** rollout. Capture before (serving) and after (hardened *and* still serving). Both, or roll the ring back.
- **The exception carve-out is a defended decision, not a silent skip** — the legacy host class the benchmark would break gets a *relaxed, documented* profile for that control, with the reason and compensating control recorded (the "accept-with-justification" ADR at fleet scale). A silent skip is a lie in the compliance report.
- **Rollback is cheap because you only changed one ring** — re-converge that ring to the previous baseline (or restore its snapshot) and it serves again in minutes while you debug one slice. The fleet is declared hardened *last*, only when every ring is across and health-checked.

## AI acceleration
A model is genuinely useful at the *planning and bookkeeping* of a fleet rollout — drafting the ring plan and host inventory, generating the `serial`/`max_fail_percentage` rolling playbook from your batch sizes, turning raw before/after health-check output into a clean no-outage proof table, and writing the health-check harness. That is real leverage on the tedious half. But the posture is strict, because the dangerous instinct is the model's default: ask it to "harden the fleet" or "apply CIS to all the servers" and it will hand you a **big-bang** playbook — one run, every host, no rings — because that's the simplest thing to express and it carries none of the operational fear of a live outage (it has no idea which of your hosts is the database serving production traffic). The judgment it cannot do for you is **sequencing by blast radius** (which hosts are safe in the test ring, what the canary fraction should be, which host class needs the exception) and, above all, **the service-health check** — asked to "confirm the rollout worked," a model checks that the Ansible run went green and the CIS score rose and calls it done, **missing entirely that the app on those hosts is now down** (compliant ≠ working, the failure mode it's blind to). Make the model draft the ring plan, the rolling playbook, and the health harness; **you** decide the ring order and the canary size, you confirm every ring has a *tested* rollback, you own the *defended* exception for the legacy host class, and you verify the after-state proves *hardened **and** still serving* before any control reaches the fleet. AI authors the runbook; you own the rollout — and the blast radius.
