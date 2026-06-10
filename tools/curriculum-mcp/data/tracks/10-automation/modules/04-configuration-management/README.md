# Module 04 — Configuration Management

*Module concept · [Go to the hands-on lab →](lab.md)*


**Security Automation** — *if you hardened it once by hand, a configuration management tool can harden a thousand more.*

## Why this matters
A server hardened manually is a server that drifts. Six months later, a junior admin adds a
package for a quick test, leaves a service running, and the hardening is partially undone. A
server hardened by Ansible is a server that can be re-hardened in minutes — and the playbook
is the auditable record of every setting and why it's there. Configuration management is how
security teams enforce policy at scale and prove it to auditors.

## Objective
Write an Ansible playbook and role structure that hardens a Linux container — SSH configuration,
package removal, sysctl settings — and prove it is idempotent: running the playbook twice
produces the same result with zero changes on the second run.

## The core idea
Ansible is an agentless configuration management tool: it connects to targets over SSH (or
Docker exec in the lab), executes modules, and reports the state of each task (OK, CHANGED,
FAILED, SKIPPED). The fundamental property that makes Ansible useful for compliance is
**idempotency** — each task checks whether the desired state already exists before making a
change. A task that sets `sshd_config PermitRootLogin no` checks the current value and only
writes if it differs. Run it a hundred times; it changes the file once. This is also how you
detect drift: if the second run shows CHANGED tasks, something changed the state between runs.

Role structure is the discipline that turns a flat playbook into a reusable, reviewable unit.
A role has `tasks/main.yml` (what to do), `handlers/main.yml` (what to do when notified, e.g.,
restart sshd after config change), `defaults/main.yml` (tunable variables with safe defaults),
and `meta/main.yml` (dependencies and metadata). This structure is not bureaucracy — it's the
interface that lets another engineer use your role without reading every task. `ansible-galaxy
install` installs a role from a URL; `ansible-galaxy role init` scaffolds the structure. Both
are standard practice.

The CIS Benchmarks are the most widely used hardening standards and the natural policy targets for
Ansible hardening roles: each benchmark item maps to one or more Ansible tasks. The `devsec.os_hardening`
Galaxy role is a community implementation of CIS Linux benchmarks — it's a good reference for
what production hardening looks like, even if you write your own for this lab.

Ansible Vault is the answer to "how do I store secrets in an Ansible playbook?" — it encrypts
variables files with a password you manage separately. Never store unencrypted secrets in a
playbook repository; if a password or API key appears in plaintext in a `vars:` block, it will
eventually end up in a git log.

## Learn (~2.5 hrs)

**Ansible fundamentals (~1.5 hrs)**
- [Ansible Getting Started — official documentation](https://docs.ansible.com/projects/ansible/latest/getting_started/index.html) — work through "Getting started with Ansible" and "Building an inventory"; understand modules, tasks, handlers, and idempotency.
- [Ansible Roles — official documentation](https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_reuse_roles.html) — the role directory structure and how to call a role from a playbook; this is the pattern the lab uses.

**Security hardening with Ansible (~1 hr)**
- [CIS Benchmarks — Center for Internet Security](https://www.cisecurity.org/cis-benchmarks/) — skim the "CIS Distribution Independent Linux Benchmark" overview; understand that each numbered item is an auditable policy requirement.
- [devsec.hardening — Ansible Galaxy](https://galaxy.ansible.com/devsec/hardening) — a mature CIS-aligned hardening role; read the README for the pattern, not to use it directly.

## Key concepts
- Idempotency: check state before changing it — CHANGED means it was wrong; OK means it was right
- Role structure: tasks / handlers / defaults / meta — the interface for reusable hardening
- Handlers: triggered by `notify`, not by every run — restart services only when config changes
- Ansible Vault for secrets: never plaintext in playbooks
- Drift detection: second run with CHANGED tasks means something changed between runs

## AI acceleration
Ansible is a natural target for AI generation — the YAML is verbose and repetitive. Ask a model
to generate the sysctl hardening tasks from a CIS Benchmark list. Then verify idempotency: run
the playbook twice and confirm the second run shows no CHANGED tasks. If it does, the task isn't
using the correct module or isn't checking state correctly. Idempotency is the test that catches
the model's mistakes in configuration management.
