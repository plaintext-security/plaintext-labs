# Module 06 — Configuration Management

*Module concept · [Go to the hands-on lab →](lab.md)*


**[Track 07 — Endpoint & Host Hardening]** — *Hardening that lives in a runbook dies in a ticket queue; hardening expressed as code survives team changes, scales to thousands of hosts, and can be tested.*

## Why this matters

The hardening you applied in modules 02–04 produces a host that is secure today. Configuration management is what keeps it secure in six months when a new team member applies a one-off change, when a package update resets a sysctl parameter, or when you need to roll the same baseline to 200 new servers. Without configuration management, hardening is a one-time event that drifts; with it, hardening is a continuous commitment that can be audited.

## Objective

Write an Ansible hardening playbook that applies five CIS-equivalent controls to a Linux host — disable root SSH, set password complexity, enable auditd, set a secure umask, and configure sysctl parameters — then run it idempotently and confirm each setting with a verification task.

## The core idea

Ansible models configuration as desired state expressed in YAML. A playbook says "this host should have these settings" — and the Ansible runner compares current state to desired state and makes only the necessary changes. Idempotency is the key property: running the same playbook twice produces the same result, with no unintended side effects on the second run. This is what separates configuration-as-code from a hardening script: a script run twice might break things on the second run; an idempotent playbook will simply confirm everything is already in place.

The Ansible playbook as a hardening artefact has three distinct advantages over a shell script. First, it is self-documenting — each task names the control it implements. Second, it is testable — you can run it against a test environment, verify with `--check` (dry-run mode), and compare before and after states. Third, it is auditable — the git history of the playbook is the change log for your hardening baseline. When an auditor asks "what changed between the January and February baseline?", the answer is a `git diff`.

Roles are the Ansible unit of reuse. A well-structured hardening playbook uses a `security` role (or the community `ansible-lockdown` roles for CIS) that can be applied to different host groups with different variable overrides. For Meridian Financial's Linux fleet, the same role applies to both developer workstations (with some controls relaxed) and production servers (at full stringency) — the variable file determines the posture; the role logic is shared. This is the "hardening as a policy parameter" model that modern security programmes use.

Drift detection is the operational complement to idempotent application. Ansible's `--check` mode reports what *would* change if the playbook ran — run it in check mode on a scheduled basis and treat any pending change as a drift alert. A playbook that reports nothing to change confirms the host is in the expected state. A playbook that reports changes reveals that someone (or some package update) has modified the configuration since the last enforcement run. Combined with the telemetry from module 05, this gives you both the configuration ground truth and the event stream that explains how it changed.

## Learn (~4 hrs)

**Ansible fundamentals**
- [Ansible Getting Started — official documentation](https://docs.ansible.com/projects/ansible/latest/getting_started/index.html) — read the "Concepts" and "Playbooks" sections (~45 min); understand inventory, playbooks, tasks, and modules before writing any hardening playbook.
- [Ansible best practices (official)](https://docs.ansible.com/projects/ansible/latest/tips_tricks/ansible_tips_tricks.html) — roles structure, idempotency, and variable management; skim (~20 min) for the structural patterns.

**Ansible for security hardening**
- [ansible-lockdown/UBUNTU22-CIS (GitHub)](https://github.com/ansible-lockdown/UBUNTU22-CIS) — a production-grade CIS role for Ubuntu 22.04; read the README and browse a few tasks in `tasks/` to understand how the community implements CIS controls as code.
- [Ansible security automation (Red Hat)](https://www.ansible.com/use-cases/security-and-compliance) — the business case and patterns for security-as-code; skim for context.

**Idempotency and testing**
- [Molecule — Ansible testing framework](https://docs.ansible.com/projects/molecule/) — the standard way to test Ansible roles against Docker containers; read the Getting Started guide for the test-driven hardening pattern.

## Key concepts

- Ansible models desired state; idempotency means running the playbook twice is safe and produces no unintended changes.
- Playbooks > scripts: named tasks, `--check` dry-run, git-tracked change history.
- Roles enable variable-parameterised policy: same role, different posture by variable file.
- `--check` mode as a drift detector: treat pending changes as drift alerts.
- The `ansible-lockdown` community maintains production-grade CIS roles — adopt before you write.

## AI acceleration

Use an AI to generate the first draft of a hardening task in Ansible YAML — describe the control in plain English ("disable root SSH login") and ask for the corresponding Ansible task. Then validate: does the module (`lineinfile`, `sysctl`, `service`) match what the task actually does? Is the idempotency condition correct (will re-running the task change anything)? Run with `--check` and compare the expected output. AI drafts the YAML; `--check` tells you if it's right.
