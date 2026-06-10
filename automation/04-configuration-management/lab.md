# Lab 04 — Configuration Management

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/04-configuration-management
make up        # Ansible controller + Ubuntu target container
make demo      # runs the hardening playbook twice to prove idempotency
make shell     # shell in controller container
make down
```

Two containers: an **Ansible controller** with `ansible` installed, and a bare **Ubuntu 22.04
target** accessible over the compose network. `data/roles/hardening/` has the scaffolded role
structure with TODOs. The demo runs the playbook twice and fails if the second run shows any
CHANGED tasks.

## Scenario
Meridian needs a repeatable hardening baseline for all Linux servers. You'll write an Ansible
role that applies the top 10 CIS Level 1 SSH and sysctl settings, then prove it's idempotent —
the audit requirement is that the same playbook can be re-run at any time to detect and correct
drift.

## Do
1. [ ] `make demo` — watch the reference playbook run twice. Note the CHANGED/OK counts in each
   run. Confirm the second run shows 0 CHANGED.
2. [ ] Open `data/roles/hardening/tasks/main.yml`. Fill in the following tasks:
   - Set `PermitRootLogin no` in `/etc/ssh/sshd_config` using `ansible.builtin.lineinfile`.
   - Set `PasswordAuthentication no` in sshd_config (same module).
   - Disable IP forwarding: `net.ipv4.ip_forward=0` using `ansible.posix.sysctl`.
   - Enable SYN cookie protection: `net.ipv4.tcp_syncookies=1` using `ansible.posix.sysctl`.
   - Remove the `telnet` package using `ansible.builtin.package`.
   - `notify: Restart sshd` on the sshd_config tasks.
3. [ ] Fill in `data/roles/hardening/handlers/main.yml` with the `Restart sshd` handler using
   `ansible.builtin.service`.
4. [ ] Fill in `data/roles/hardening/defaults/main.yml` with a `sshd_port` variable (default 22)
   and use it in the tasks — demonstrating parameterization.
5. [ ] Run `make demo` against your role — confirm both runs pass and the second shows 0 CHANGED.
6. [ ] Manually change one setting on the target (`docker compose exec target sed -i 's/no/yes/'
   /etc/ssh/sshd_config`) and re-run the playbook — confirm it detects and corrects the drift.

## Success criteria — you're done when
- [ ] First playbook run: all tasks CHANGED or OK (no FAILED).
- [ ] Second playbook run: 0 CHANGED tasks (fully idempotent).
- [ ] After manual drift: one CHANGED task that corrects it.
- [ ] `sshd_port` variable is used in at least one task.

## Deliverables
`data/roles/hardening/` (all files). Commit the entire role directory.

## Automate & own it
**Required.** Add a CI check: write a `Makefile` target `idempotency-check` that runs the
playbook twice with `ansible-playbook --diff` and fails if the second run outputs "changed=".
Have a model draft the shell command that parses ansible output for changed tasks; test it
manually. Commit the target.

## AI acceleration
Ask a model to generate the sysctl hardening tasks from a list of CIS Linux Benchmark
recommendations. Verify each task: does it use `ansible.posix.sysctl` (which handles
`/etc/sysctl.conf` persistently) or `command: sysctl -w` (which is not idempotent and not
persistent)? The choice of module is the difference between a hardening task and a hardening
illusion.

## Connects forward
The role structure from this module is the template for the CI/CD pipeline in module 05, which
gates changes to Ansible roles before they run in production. In Track 07 (Endpoint Hardening),
the same Ansible patterns apply at scale.

## Marketable proof
> "I write idempotent Ansible roles for Linux hardening — I can prove drift detection works by
> re-running the playbook and reading the CHANGED count, and I can explain every task to an auditor."

## Stretch
- Add a `verify.yml` that runs after the playbook and asserts the expected state using
  `ansible.builtin.assert` — turning the playbook into a test harness for compliance.
- Use `ansible-lint` to check the role for best-practice violations before running it.
