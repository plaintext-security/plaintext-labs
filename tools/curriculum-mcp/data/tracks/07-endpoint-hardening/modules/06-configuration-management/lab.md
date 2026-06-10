# Lab 06 — Configuration Management

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/endpoint-hardening/06-configuration-management
make up        # build the Ansible controller + target containers
make demo      # run the hardening playbook and show changes applied
make shell     # drop into the Ansible controller
make down      # stop when done
```

> Everything runs locally. The controller runs Ansible against a target container on the
> Docker bridge network. No external hosts targeted.

## Scenario

Meridian Financial has approved a hardening playbook for all Ubuntu 22.04 application servers.
You are the security engineer responsible for writing it, testing it for idempotency, and
validating that each control is actually applied. The playbook will be committed to the
infrastructure-as-code repo and run by the CI/CD pipeline on every new host provision.

## Do

1. [ ] `make demo` — watch the playbook run and note: which tasks report `changed` on the first
   run, and which report `ok`. Record the task names and their status.

2. [ ] `make demo` again immediately — confirm that every task now reports `ok` (idempotency).
   If any task still reports `changed` on the second run, that is a bug: find and fix it.

3. [ ] `make shell` to enter the Ansible controller, then explore the playbook:
   ```bash
   cat /lab/data/playbook.yml
   ```
   For each of the five tasks, answer:
   - What CIS control does it implement?
   - What Ansible module does it use?
   - What check does the verify task at the end perform?

4. [ ] Add a sixth task to the playbook: ensure `fail2ban` is installed and enabled. Write the
   task, run the playbook (`ansible-playbook -i inventory data/playbook.yml`), and confirm the
   `changed` → `ok` idempotency cycle.

5. [ ] Run the playbook in check mode against the target:
   ```bash
   ansible-playbook -i inventory data/playbook.yml --check
   ```
   Observe the "would change" output. Now deliberately modify a setting on the target
   (e.g. `ansible target -m shell -a "sed -i 's/PermitRootLogin no/PermitRootLogin yes/' /etc/ssh/sshd_config"`)
   and re-run `--check`. Observe the drift report.

6. [ ] Write a `drift-check.sh` script that runs the playbook in `--check` mode, captures
   the output, and prints a one-line summary: "COMPLIANT" if no tasks would change, or
   "DRIFT DETECTED: N tasks would change" if any would.

## Success criteria — you're done when

- [ ] The playbook runs with all five original tasks idempotent (all `ok` on second run).
- [ ] You added a sixth task (`fail2ban`) that also passes the idempotency test.
- [ ] You used `--check` mode to detect a deliberate drift and confirmed the detection.
- [ ] `drift-check.sh` exits non-zero when drift is present.

## Deliverables

`playbook.yml` (your extended, six-task version) + `drift-check.sh`. Commit both.

## Automate & own it

**Required.** Wire `drift-check.sh` into a GitHub Actions workflow that runs on a schedule
(cron: daily) against a test container. The workflow should fail if drift is detected, producing
an alert that someone changed the baseline. Have an AI draft the workflow YAML; you verify the
trigger, the container setup, and the exit-code check before committing.

## AI acceleration

Describe a CIS control in plain English to an AI (e.g. "Set the minimum password length to 14
in PAM on Ubuntu 22.04") and ask for the Ansible task. Then:
1. Check the Ansible module name is real and current (cross-check against [docs.ansible.com](https://docs.ansible.com/)).
2. Run with `--check` to confirm the dry-run output makes sense.
3. Run for real and `--check` again to confirm idempotency.
The model drafts the YAML; you own the test cycle.

## Connects forward

The Ansible playbook you write here is the "hardening as code" foundation that module 07
(compliance auditing) measures — you now have a reproducible baseline to audit against and
a drift detector to confirm it. Module 08 (patch management) extends the playbook with
package-update tasks.

## Marketable proof

> "I wrote an idempotent Ansible hardening playbook for five CIS controls, validated drift
> detection with --check mode, and wired it into CI so every host provision is verifiably
> compliant."

## Stretch

- Convert the playbook into an Ansible role with a `vars/` file for the policy settings
  (password length, umask value, etc.). Apply the role twice with different variable files to
  show how the same role produces workstation vs. server postures.
- Add Molecule tests to the role: write a `verify.yml` that checks each control is actually
  applied after the role runs, and confirm `molecule test` passes.
