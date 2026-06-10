# Module 10 — Hardening AD as Code

*Module concept · [Go to the hands-on lab →](lab.md)*


**Active Directory & Windows Security** — *every misconfiguration found in modules 02-09 has a fix; this module turns those fixes into code that can be deployed, reviewed, and re-run.*

## Why this matters

Security hardening that lives in a checklist in a SharePoint site will drift. Group Policy changes made in the console are unversioned. An AD hardening posture that cannot be measured cannot be improved. The principle is the same as detection-as-code: if the hardening isn't in version control, it isn't real. This module operationalises the mitigations from the attack path — GPO settings, ACL corrections, account attribute changes — as Ansible tasks and scored checks that can be run on a schedule.

## Objective

Audit the Meridian domain's ACL posture using `dacledit.py`, produce a scored hardening report against a CIS-aligned checklist, and write an Ansible playbook that codifies the key remediations as idempotent, reviewable tasks.

## The core idea

The gap between "we know what to fix" and "it's actually fixed" in an AD environment is bridged by two practices: **automated posture measurement** and **configuration-as-code**. Automated posture measurement means running a script that queries the domain for known-bad configurations (Kerberoastable service accounts, accounts without pre-auth, unconstrained delegation, ACL misconfigurations, missing GPO settings) and produces a score. Configuration-as-code means expressing the remediations as idempotent scripts or playbooks that can be applied, reviewed in pull requests, and re-run to verify they took effect.

Tools like PingCastle (Windows-only, freemium) do automated AD posture scoring; for a Linux-friendly, open-source equivalent, `dacledit.py` (from impacket) reads object ACLs, and `ldapsearch`-based scripts can audit the user attributes that expose the domain to attack. The posture audit is not a one-time engagement deliverable — it should run on a schedule (weekly or after any significant change) and generate a delta report: "we had three Kerberoastable accounts last week; we have one now." That delta is how you demonstrate progress.

The Ansible approach works because AD objects are ultimately LDAP objects, and Ansible's `community.windows` collection has modules for GPO management (`win_gpo`), AD user manipulation (`win_user`, `microsoft.ad.user`), and group membership (`microsoft.ad.group`). An Ansible task that reads "ensure svc-legacy has DONT_REQUIRE_PREAUTH=False" is precise, reviewable by a security team, and verifiable by re-running with `--check`. The same playbook that applies the hardening can document it — each task's `name:` field is the human-readable audit trail.

The CIS Benchmark for Active Directory covers hundreds of controls, but the 20 that matter most in a typical environment are all in the same territory as the attacks you've learned: service account password age, SPN hygiene, delegation settings, privileged group membership, GPO audit policy coverage, and SMB signing. Hardening-as-code that covers those 20 controls, deployed and running in CI, is more valuable than a 200-item checklist nobody re-checks.

## Learn (~3 hrs)

**AD posture assessment tools**
- [PingCastle — AD Risk Assessment (pingcastle.com)](https://www.pingcastle.com/) — the most widely used AD posture tool. Free community edition runs on Windows; understand the scoring methodology and risk categories even if you use impacket equivalents for the lab.
- [dacledit.py (impacket GitHub)](https://github.com/fortra/impacket/blob/master/examples/dacledit.py) — the Python-native ACL editor and reader; used in the lab to audit ACEs on AD objects. Read the `--action read` usage.

**CIS benchmark**
- [CIS Microsoft Windows Server 2019 Benchmark (CIS)](https://www.cisecurity.org/benchmark/microsoft_windows_server) — free download (registration required). Focus on the Active Directory-specific sections: account policies, Kerberos settings, audit policies, group memberships. Use as the reference for the hardening checklist.

**Ansible for Windows/AD**
- [Ansible — microsoft.ad collection (Galaxy docs)](https://docs.ansible.com/projects/ansible/latest/collections/microsoft/ad/) — the official AD collection. The `microsoft.ad.user` and `microsoft.ad.group` modules are the primary ones for this module. Read the parameter documentation.

## Key concepts
- Posture measurement = automated query against the domain for known-bad configurations, scored and trended.
- Configuration-as-code for AD = Ansible tasks over WinRM or LDAP; idempotent and reviewable.
- The 20 highest-priority controls: service account password age, SPN hygiene, no-preauth accounts, unconstrained delegation, privileged group membership, GPO audit coverage, SMB signing.
- PingCastle scores posture on a 0-100 scale (lower is better/riskier); use the risk categories as a priority guide.
- Hardening playbooks should be in version control and run with `--check` before applying.
- Delta reporting (this week vs. last week) is how you demonstrate remediation progress.

## AI acceleration

Ask a model to generate an Ansible playbook from the mitigation list in module 08. The model is good at Ansible YAML structure but will often use deprecated module names (e.g., `win_ad_user` instead of `microsoft.ad.user`) or incorrect parameter names. Validate every module name and parameter against the Galaxy docs before running `--check`. The draft is a starting point, not a finished playbook.
