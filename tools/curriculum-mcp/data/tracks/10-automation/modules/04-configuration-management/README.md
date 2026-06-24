# Module 04 — Configuration Management & Drift

*Type 7 · Build-&-Operate — write idempotent configuration that converges a host to a known-good state and reconciles drift; the deliverable is the config plus a proven t=0-fine / t=30-drifted / reconcile loop. (Secondary: Drift / Steady-State.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Security Automation** — *hardening a server once is the easy part; the job is keeping it hardened while everyone keeps touching it.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~4–5 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters
You harden a server today. CIS Level 1, by the book — root SSH off, password auth off,
IP forwarding disabled, telnet gone. It passes the audit. Thirty days later it's wrong again,
and nobody decided to make it wrong. A junior admin re-enabled password auth to debug a login
at 2 a.m. and never reverted it. A package install pulled in a service that flipped a sysctl.
A "temporary" firewall change outlived the ticket. The host didn't get *attacked* — it **drifted**,
and the security control you proved last month is silently gone.

This is not a corner case; it is the single most common way controls fail. When CISA and the NSA
red and blue teams published their **Top Ten Cybersecurity Misconfigurations** advisory
([AA23-278A](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-278a), 2023) — the most
frequent weaknesses they found across hundreds of real assessments — the list is almost entirely
*drift*: hosts that started from a hardened image and slowly diverged into default credentials,
flat networks, and missing patches through untracked manual change. Martin Fowler named the failure
mode years earlier: the **snowflake server** — a one-of-a-kind box "grown" through ad-hoc CLI
commands and console edits until nobody can reproduce it or say what's true on it
([SnowflakeServer](https://martinfowler.com/bliki/SnowflakeServer.html)). The opposite — a host you
can rebuild or re-prove from a declared spec at will — he calls a **phoenix**. *"Drift is the name of
the street that leads to snowflake servers."*

Configuration management is how you stay on the phoenix side. Writing the playbook once is table
stakes. The skill that matters in production — and the one this module builds — is the **closed loop**:
declared baseline → detect when reality has wandered off it → reconcile back. "Set and forget" *is*
the failure.

## Objective
Build a hardened Linux baseline as an idempotent Ansible role, then **build the drift loop around it**:
introduce an out-of-band change to the hardened host, **detect** the delta against the declared state
(`ansible-playbook --check --diff`), **report** what drifted, **reconcile** it back, and **prove
steady-state**. The deliverable is the drift detector + the reconciliation run — not just a playbook
that runs clean once.

## The core idea
**Idempotency is the property; the drift loop is what you do with it.** An Ansible task is *idempotent*
when it checks the current state before acting: a task that sets `PermitRootLogin no` reads the file,
and only writes if the value differs. Run it once or a hundred times — the file changes once. Each task
reports `OK` (already correct), `CHANGED` (it was wrong, now fixed), `FAILED`, or `SKIPPED`. That status
line is not just noise — it is a **diff between declared state and observed state**, and that diff is the
whole game.

Read it that way and configuration management becomes a control loop, not a one-shot installer:

- **Declared state** — the role *is* the spec. `tasks/main.yml`, `handlers/main.yml`,
  `defaults/main.yml`, `meta/main.yml`: the auditable record of every setting and why it exists. This is
  the phoenix's source of truth.
- **Detect (the load-bearing move)** — running the playbook with `--check --diff` is a **dry run**: Ansible
  reports what it *would* change without changing anything, and `--diff` shows the before/after line. Any
  task that reports `changed` in check mode is **drift** — the host has wandered off the declared spec.
  A green `--check` (zero changed) is a *proof of steady-state* you can hand an auditor. This is the
  detector, and it costs you nothing because the idempotent role you already wrote *is* the spec to
  compare against.
- **Reconcile** — drop `--check`, re-run, and the same idempotent tasks pull the host back to declared
  state. Detection and correction are the *same playbook* in two modes. That symmetry is the elegant part:
  you don't write a separate scanner, you run your spec in read-only mode.
- **Re-enforce on a schedule** — the loop only protects you if it runs *without* a human deciding to run
  it. Fowler's **configuration synchronization** is exactly this: the tool "continually applies the
  specification... on a regular schedule" so drift is caught in hours, not at the next breach
  ([ConfigurationSynchronization](https://martinfowler.com/bliki/ConfigurationSynchronization.html)). A
  scheduled `--check` that alerts on non-zero changes is a drift *monitor*; a scheduled enforcing run is
  *self-healing*. Which one you want is a real judgment — auto-reconcile is powerful and occasionally
  dangerous (it will happily revert a legitimate emergency change nobody encoded yet), so production teams
  often run `--check`/alert in prod and full enforcement in lower environments. Either way: **the loop runs
  itself, or it isn't a control.**

The one load-bearing judgment of this module: **detect-only vs auto-reconcile.** A drift *detector* that
pages a human respects that the host may have drifted for a good reason; an *enforcer* that silently
reverts removes the security gap fast but can stomp an undocumented fix. State which you chose and why —
that choice *is* your operating posture, and it's exactly what an auditor will ask about.

Two supporting tools make this real rather than a toy. The **CIS Benchmarks** are the natural policy
target: each numbered item maps to one or more tasks, so your role is auditable against a published
standard rather than your own taste; the `devsec.hardening` Galaxy role is a mature reference for what
production CIS hardening looks like. And **Ansible Vault** is the answer to secrets in the spec: encrypt
any credential a play needs, because a plaintext password in a `vars:` block *will* end up in git history.

## Learn (~2.5 hrs)

*Lean on purpose — the loop above is yours to own. These go deeper on the Ansible mechanics and the drift
concept; read them to build the lab, not to relearn the model.*

**Ansible mechanics (~1.5 hrs)**
- [Ansible — Getting Started](https://docs.ansible.com/projects/ansible/latest/getting_started/index.html) (~45 min, do it) — work "Getting started" + "Building an inventory" until modules, tasks, handlers, and idempotency are muscle memory; this is the spec language.
- [Ansible — Roles](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_reuse_roles.html) (~25 min) — the `tasks/handlers/defaults/meta` directory contract and how a playbook calls a role; the exact structure the lab uses as its declared state.
- [Ansible — Validating tasks: check mode and diff mode](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_checkmode.html) (~20 min, **the key page for this module**) — `--check` (dry run) and `--diff`; this *is* your drift detector. Read how `changed` in check mode means "would change," i.e. drift.

**Drift as a discipline (~45 min)**
- [Martin Fowler — Snowflake Server](https://martinfowler.com/bliki/SnowflakeServer.html) + [Configuration Synchronization](https://martinfowler.com/bliki/ConfigurationSynchronization.html) (~15 min, both short) — the canonical mental model: why ad-hoc-edited hosts can't be reproduced, and the continual-apply loop that fixes it. Short, primary, worth it.
- [CISA/NSA — Top Ten Cybersecurity Misconfigurations (AA23-278A)](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-278a) (~30 min, skim the ten + the mitigations) — the field evidence that drift is the dominant real-world failure; read it as "this is what hosts look like after a year of un-reconciled change."
- [CIS Benchmarks — overview](https://www.cisecurity.org/cis-benchmarks/) (~10 min, skim) — that each numbered item is an auditable requirement your role maps to; the policy target your declared state encodes.

## Key concepts
- **Declared vs observed state** — the role is the spec; the host is reality; the gap between them is drift
- **The `CHANGED` line is a diff** — `OK` = matched declared, `CHANGED` = was wrong and got corrected
- **`--check --diff` is the detector** — a dry run; any `changed` in check mode is drift, zero changed is steady-state proof
- **Detect and reconcile are one playbook in two modes** — read-only (`--check`) vs enforcing — you don't write a separate scanner
- **The loop must run unattended** — scheduled re-enforcement (configuration synchronization); "set and forget" is the failure
- **Detect-only vs auto-reconcile** — the load-bearing posture choice: alert-a-human vs silently self-heal, each with honest tradeoffs
- **Idempotency is the enabler** — without it, re-running can't be a safe detector or a safe corrector
- **CIS Benchmarks** as the policy target; **Ansible Vault** so secrets in the spec never hit plaintext/git

## AI acceleration
Ansible YAML is verbose and repetitive — exactly what a model drafts well and exactly where it slips. Ask a
model to generate the sysctl and SSH hardening tasks from a list of CIS items; it will produce plausible
YAML fast. Then **review every line against one test: is it idempotent?** The classic model failure here is
reaching for `ansible.builtin.command: sysctl -w net.ipv4.ip_forward=0` instead of `ansible.posix.sysctl` —
the first is *not* idempotent (it reports `changed` every run and doesn't persist), which silently breaks
your drift detector, because now *every* `--check` shows a false positive and real drift hides in the noise.
The detector you build in the lab is itself the test that catches the model's mistake: run the AI-drafted
role twice; if the second run isn't zero-changed, the model handed you a hardening *illusion*. AI drafts →
you verify idempotency → you own the loop.
