# Lab 04 — Configuration Management & the Drift Loop

*Hands-on lab · Type 7 Build-&-Operate + Type 16 Drift/Steady-State · [← Back to the module concept](README.md)*

## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/04-configuration-management
make up        # Ansible controller + Ubuntu 22.04 target container
make demo      # harden the target, then run the full drift loop end-to-end
make shell     # shell in the controller container
make down
```

Two containers on a compose network: an **Ansible controller** (`ansible` + `ansible-lint`) and a
bare **Ubuntu 22.04 target** that boots in a deliberately *un-hardened* state (root SSH and password
auth enabled, `telnet` present). `data/roles/hardening/` holds the role you'll complete — this is your
**declared state**. The Makefile carries the loop targets: `harden`, `drift-check`, `inject-drift`,
`reconcile`, and `steady-state`.

## Scenario
You're the platform engineer who owns the Linux hardening baseline for a fleet. Hardening the box once
is the easy half — you've been told the audit finding that actually keeps recurring is *snowflake
servers*: hosts that were hardened months ago and have since drifted, silently, back toward insecure
defaults through untracked manual change (the CISA/NSA Top Ten Misconfigurations shape). Your job is to
build the **closed loop** that keeps the host on-spec: declare the baseline, detect when reality wanders
off it, reconcile it back, and prove it's quiet — all repeatably, all without a human deciding to look.

> **Authorization:** this lab attacks only the disposable target container the compose file creates on
> your own machine. The "out-of-band change" you inject is on that container. Only ever run drift
> detection/enforcement against systems you own or have explicit written permission to manage.

## Do

### Stage 1 — Declare the baseline (build the spec)
1. [ ] `make demo` once to watch the whole loop run with the reference role; note the shape of each stage.
   Then `make down && make up` to reset and do it yourself.
2. [ ] Complete `data/roles/hardening/tasks/main.yml` so the host matches CIS Level 1 essentials. Each task
   must be **idempotent** — pick the module that checks state before changing it:
   - `PermitRootLogin no` and `PasswordAuthentication no` in `/etc/ssh/sshd_config` (`ansible.builtin.lineinfile`), each `notify: Restart sshd`.
   - `net.ipv4.ip_forward=0` and `net.ipv4.tcp_syncookies=1` (`ansible.posix.sysctl`, `sysctl_set: true`).
   - Remove `telnet` (`ansible.builtin.package`, `state: absent`).
3. [ ] Fill `handlers/main.yml` (`Restart sshd`) and use the `sshd_port` default from `defaults/main.yml` in
   at least one task — this is your spec's tunable surface.
4. [ ] `make harden` — apply the role. Confirm tasks report `CHANGED`/`OK`, none `FAILED`.

### Stage 2 — Prove steady-state (the detector, baseline reading)
5. [ ] `make drift-check` — this runs the playbook with `--check --diff` (a **dry run**: detect, don't
   change). On a freshly-hardened host it must report **0 changed**. That zero *is* your steady-state proof.
   Read what the target said: "I am on-spec."

### Stage 3 — Introduce drift (out-of-band change to a hardened host)
6. [ ] `make inject-drift` — simulates the 2 a.m. manual change: it flips `PasswordAuthentication` back to
   `yes` on the target, *out of band*, the way a real admin would with `sed`/an editor — bypassing Ansible
   entirely. The host is now silently insecure; nothing in your spec changed, but reality did.

### Stage 4 — Detect & report the delta
7. [ ] `make drift-check` again. This time it reports **non-zero changed**, and `--diff` shows the exact
   line that drifted (`PasswordAuthentication yes` → `no`). This is detection: declared vs observed, with
   the delta named. Capture this output — it is half your deliverable (the *report*).

### Stage 5 — Reconcile & re-prove steady-state
8. [ ] `make reconcile` — run the playbook *enforcing* (no `--check`). The same idempotent task that detected
   the drift now corrects it: exactly **one** `CHANGED` (the drifted setting), sshd restarts via the handler.
9. [ ] `make steady-state` — run `drift-check` one final time. Back to **0 changed**. You've closed the loop:
   detect → diff → reconcile → re-prove. Capture this output too — the loop is *proven*, not asserted.

### Stage 6 — Make the loop run itself (and own the posture choice)
10. [ ] Decide your operating posture and write it down (one paragraph in `LOOP.md`): **detect-only** (the
    scheduled job runs `--check` and alerts on non-zero, a human reconciles) **vs auto-reconcile** (the
    scheduled job enforces and self-heals). State the tradeoff you accept — an enforcer closes the gap fast
    but can stomp an undocumented emergency fix; a detector respects that but leaves the host insecure until
    someone acts. There is no universally right answer; defend yours.

## Success criteria — you're done when
- [ ] After `make harden`, a `make drift-check` reports **0 changed** (steady-state proven).
- [ ] After `make inject-drift`, `make drift-check` reports **non-zero changed** and the `--diff` names the
  exact drifted setting (detection works, with a readable delta).
- [ ] `make reconcile` corrects it with **exactly one** `CHANGED` task, and the *next* `drift-check` is back
  to **0 changed** (reconciliation + re-proof).
- [ ] The second run of the *enforcing* playbook on an un-drifted host is **0 changed** (idempotent — the
  detector has no false positives).
- [ ] `LOOP.md` states your detect-only-vs-auto-reconcile choice and its honest tradeoff.

## Deliverables
Commit:
- `data/roles/hardening/` — the complete role (your declared state).
- **`drift-detect.sh`** — the drift detector (see *Automate & own it*): runs the check-mode loop, parses the
  result, exits non-zero on drift, prints the delta.
- **`LOOP.md`** — the captured before/after of one full loop (steady → injected drift → detected delta →
  reconciled → steady) and your posture paragraph.

The role + the detector + the reconciliation evidence is the artifact — *not* an idempotent playbook on its
own. (Lab artifacts — target shell history, captures — stay out of commits.)

## Automate & own it
**Required.** Turn the loop into a single committed tool, `drift-detect.sh`, that a scheduler could call
unattended:
1. Run the playbook in check mode (`ansible-playbook ... --check --diff`), capture stdout.
2. Parse the per-host recap for `changed=[1-9]`; on drift, **exit non-zero** and print the offending host(s)
   and the `--diff` lines (so the alert says *what* drifted, not just *that* it did).
3. Add an optional `--reconcile` flag that, on detected drift, re-runs enforcing and re-checks — this is the
   detect-only-vs-auto-reconcile switch from Stage 6, in code.

Have a model draft the output-parsing (it's fiddly), then **review it line by line**: the parser must not
treat an *expected* re-harden as a false alarm, and must fail closed (non-zero) if the playbook itself
errors. Wire it as `make drift-detect` (and a `make steady-state` that asserts 0 changed). This is the
difference between "we have a hardening playbook somewhere" and "we have a control that proves itself."

## AI acceleration
Ask a model to generate the sysctl hardening tasks from a CIS list, then audit the one thing that breaks the
whole loop: **module choice.** `ansible.posix.sysctl` is idempotent and persistent; `command: sysctl -w` is
neither — it reports `changed` every run, which poisons your detector with permanent false positives so real
drift hides in the noise. Your Stage-2 `drift-check` *is* the test: if a freshly-hardened host isn't 0-changed,
the model handed you a non-idempotent task. AI drafts the YAML → you prove idempotency → you own a detector
you can trust.

## Connects forward
The role here is the declared state that the **CI/CD pipeline (module 05)** gates before it reaches a host,
and the same detect→reconcile loop is the shape **endpoint hardening** uses at fleet scale and **cloud
posture management** uses against live cloud config. Drift detection is a control pattern, not an Ansible
trick — you'll meet it again wherever "we hardened it once" meets "is it still hardened?"

## Marketable proof
> "I don't just write idempotent Ansible roles — I run the drift loop: declared baseline, scheduled
> `--check --diff` detection, reconciliation, and a steady-state proof. I can show you a host drift out of
> compliance and my detector catch it, name the delta, and pull it back — and I can defend why I run
> detect-only in prod versus auto-reconcile in staging."

## Stretch
- Add a `verify.yml` that asserts expected end-state with `ansible.builtin.assert` — an independent compliance
  check that doesn't trust the role's own recap.
- Schedule the detector (a `cron` line / systemd timer in the controller) and have it write a timestamped
  drift report to a log on each run — the unattended monitor the module argues a control must be.
- Run `ansible-lint` over the role and fix what it flags before you trust the detector.
