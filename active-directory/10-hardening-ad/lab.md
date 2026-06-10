# Lab 10 — Hardening AD as Code

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/active-directory/10-hardening-ad
make up      # start the Samba4 DC + hardening-tools container
make demo    # run dacledit ACL audit against the Meridian DC
make shell   # interactive shell
make down
```

The lab includes:
- Samba4 DC with the Meridian misconfigurations from modules 02-09.
- A tools container with `dacledit.py`, `ldapsearch`, and Ansible.
- `data/hardening-checklist.md` — a CIS-aligned AD hardening checklist with the Meridian gap analysis.
- `data/ad-hardening.yml` — a starter Ansible playbook documenting remediations as tasks.

> All hardening is against your own lab domain. No external targets.

## Scenario

You are the AD hardening lead at Meridian Financial, following the red team engagement from modules 02-08. Your job: run an automated posture audit to score the current state, identify the highest-risk findings, and produce an Ansible playbook that remediates the top 5 findings. The playbook should be reviewable, idempotent, and verifiable.

## Do

1. [ ] **Run the ACL posture audit.** Read the ACLs on the three highest-risk objects (start with `IT-Admins`) with `dacledit.py`. Identify: which principals have write rights, and do any non-default accounts appear?

2. [ ] **Audit Kerberoastable accounts.** Run the ldapsearch from module 02 for SPNs. Count the accounts and their password ages from `data/meridian-domain.md`. Score: 3 Kerberoastable accounts with multi-year-old passwords = HIGH risk.

3. [ ] **Audit no-preauth accounts.** Query for `DONT_REQUIRE_PREAUTH`. Two accounts = HIGH risk.

4. [ ] **Audit unconstrained delegation.** Query for the delegation flag. One non-DC account = HIGH risk.

5. [ ] **Review `data/hardening-checklist.md`.** Go through each item. For the Meridian domain, mark each as: Compliant / Non-compliant / Not Applicable. Calculate a rough score (compliant / total applicable).

6. [ ] **Review and extend `data/ad-hardening.yml`.** Open the Ansible playbook. It documents the remediations as tasks, with `ansible.builtin.debug` tasks that print what the real remediation would do (since we can't apply changes via WinRM to a Samba4 container in this lab without extra setup). Add at least two tasks:
   - A task to remove the `DONT_REQUIRE_PREAUTH` flag from `svc-legacy`
   - A task to rotate `svc-mssql`'s password to a random 25-char value

   Have a model draft the task YAML; you verify the module name and parameter names against the Galaxy docs.

7. [ ] **Write the posture delta.** Before and after applying the playbook (conceptually), what would the posture score change be? How many attack paths from module 08 would be broken?

## Success criteria — you're done when

- [ ] You have run `dacledit.py` and identified the ACL misconfigurations.
- [ ] You have a completed posture checklist with Meridian compliance scores.
- [ ] The Ansible playbook has at least 7 tasks (5 from the starter + 2 you added).
- [ ] Each task has a descriptive `name:` and the correct module + parameters.
- [ ] You have a written posture delta: how many risks are resolved by the playbook?

## Deliverables

`data/hardening-checklist.md` (with your Meridian compliance annotations) + `data/ad-hardening.yml` (extended with your tasks) + `posture-report.md` (the scored gap analysis and posture delta). Commit all three.

## Automate & own it

**Required.** Write `posture-audit.py` — a Python script that queries the DC via ldap3 and produces a scored posture report: checks for each risk category (Kerberoastable SPNs, no-preauth accounts, unconstrained delegation, privileged group size, GPO audit status), with a pass/fail and a severity rating. Have a model draft the LDAP queries for each check; you verify the filter strings and the flag values (e.g., `userAccountControl` bit values) against the Microsoft documentation. The output should be a clean, machine-readable JSON report. Commit it.

## AI acceleration

Paste the hardening checklist items into a model and ask it to generate Ansible tasks for each. Review each task's module name against the `microsoft.ad` collection docs — the model frequently uses `win_*` module names that have been replaced. Also ask the model to add `--check`-mode compatibility to each task (idempotent, doesn't change state on a check run).

## Connects forward

The posture audit script becomes the recurring measurement tool in module 11. The Ansible playbook is the "harden as code" deliverable for the track capstone. The detection rules from module 09 + the hardening from this module together define the "before and after" posture story.

## Marketable proof

> "I run automated Active Directory posture audits with dacledit and custom scripts, score findings against a CIS-aligned checklist, and express remediations as an Ansible playbook — reviewable, idempotent, and ready for a pull request."

## Stretch

- Integrate the posture audit script into GitHub Actions: on every push, run the audit against the Samba4 lab DC (using `make up` in CI) and post the score as a PR comment. Research whether Ansible's `--check` mode can be used in CI to validate playbook syntax without applying changes.
- Research **LAPS** (Local Administrator Password Solution) deployment via Ansible. Write a task that deploys the LAPS GPO setting to the Finance OU computer objects. What does LAPS prevent? What does it not prevent?
