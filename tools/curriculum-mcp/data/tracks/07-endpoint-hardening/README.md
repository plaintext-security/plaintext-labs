# Track 07 — Endpoint & Host Hardening

**Make the host expensive to attack and loud when attacked.** Harden Windows and Linux to
recognised benchmarks — as code, with compliance scoring and drift detection.

## What you'll be able to do
- Threat-model the endpoint and prioritise what actually matters.
- Harden Windows and Linux to CIS benchmarks, expressed as code.
- Score compliance and detect configuration drift.
- Stand up endpoint telemetry that catches what hardening doesn't stop.

## Modules

| # | Module | What you'll learn | OSS tools |
|---|--------|-------------------|-----------|
| 01 | [Threat Model of the Endpoint](modules/01-endpoint-threat-model/README.md) | What you're defending and from what | — |
| 02 | [Windows Hardening to CIS](modules/02-windows-hardening/README.md) | Baseline configuration that holds up | `LGPO`, CIS-CAT-lite |
| 03 | [Linux Hardening to CIS](modules/03-linux-hardening/README.md) | Securing the Linux host as a baseline | `OpenSCAP`, `Lynis` |
| 04 | [Exploit Mitigation & Allowlisting](modules/04-exploit-mitigations/README.md) | ASLR/DEP, app control, attack-surface reduction | `AppLocker`, `fapolicyd` |
| 05 | [Endpoint Telemetry & EDR](modules/05-endpoint-telemetry/README.md) | Visibility into process/file/auth events | `osquery`, `wazuh` |
| 06 | [Configuration Management](modules/06-configuration-management/README.md) | Hardening at scale, as code | `ansible` |
| 07 | [Compliance Scoring & Auditing](modules/07-compliance-auditing/README.md) | Measuring posture against a benchmark | `OpenSCAP` |
| 08 | [Patch & Vulnerability Management](modules/08-patch-vuln-management/README.md) | Finding and closing exposure | `osquery`, `grype` |
| 09 | [Local Privilege-Escalation Defense](modules/09-privesc-defense/README.md) | Closing the paths Track 01 abuses | — |
| 10 | [Detecting Host Compromise](modules/10-detecting-host-compromise/README.md) | Catching what the baseline didn't stop | `wazuh`, `sigma` |
| 11 | [Host & Boot Integrity](modules/11-host-boot-integrity/README.md) | Proving files and the boot chain haven't been tampered with | `aide`, Secure Boot/TPM |

## Phases & projects

The eleven modules run in three phases; each ends in a **project** that integrates its modules (a phase
is the substantial, standalone unit — a single module is a few hours). Work on VMs you own, and
snapshot before destructive changes.

- **Phase 1 · Model & baseline** (01–04) — **Project:** an endpoint threat model that drives a CIS
  baseline applied to a Windows *and* a Linux host — including exploit mitigations and application
  allowlisting — with each control justified against the model.
- **Phase 2 · Scale, score & patch** (05–08) — **Project:** stand up endpoint telemetry, push the
  baseline at scale with Ansible, score compliance with OpenSCAP, and run a patch/vuln-management
  loop — proving drift detection catches a deliberate misconfiguration.
- **Phase 3 · Detect & defend** (09–11) — close the local privilege-escalation paths Track 01 abuses,
  catch a simulated host compromise with telemetry, and prove files and the boot chain are intact with
  file-integrity monitoring. **Project:** the track capstone — deliver the config-as-code, the
  before/after score delta, the detection, and a tamper-evident integrity baseline.

## Prerequisites
Complete Track 00 — Foundations first.

> Work on VMs or containers you own. Some hardening is destructive — snapshot first.

## Capstone
Harden a Windows and a Linux host to CIS as code, score the before/after compliance, prove
drift detection catches a deliberate misconfiguration, and show telemetry firing on a
simulated attack. **Deliverable:** the config-as-code, the score delta, and the detection.

The starter scaffold and acceptance checks live in
[`plaintext-labs/endpoint-hardening/capstone/`](https://github.com/plaintext-security/plaintext-labs/tree/main/endpoint-hardening/capstone).

### Capstone rubric

Harden **both** a Windows and a Linux host, and prove the baseline holds *and* drift is caught.
**Proficient is the bar to ship.**

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **Hardening coverage** | One OS, or partial baseline | Both Windows and Linux hardened to a CIS profile, expressed as code (Ansible/GPO/SCAP) | Profile tailored to a threat model — exceptions justified, not blind benchmark application |
| **Compliance scoring** | No score, or score not reproducible | OpenSCAP/CIS-CAT score before and after, with the delta documented | Failing controls triaged (fix vs. accept-with-reason); score re-run from clean state |
| **Drift detection** | None | A deliberate misconfiguration is introduced and the tooling flags it | Drift detection is automated/scheduled and reports *what* changed, not just *that* it did |
| **Telemetry** | No telemetry, or fires on nothing | Endpoint telemetry catches a simulated attack the baseline didn't stop | Detection mapped to ATT&CK and tuned against benign noise |
| **As-code & reproducibility** | Manual steps | A reader can re-apply the baseline from the committed code | One command re-hardens a fresh host and re-scores it; idempotent |

## AI & automation
AI generates the hardening (Ansible, GPO, SCAP profiles) — and that's exactly where silent
mistakes hide. The skill is reviewing generated configuration against the benchmark and
your threat model before it ships. AI authors the baseline; you own what it breaks.

## Standards & further reading
- CIS Benchmarks (Windows, Linux) and the CIS Controls
- NIST SP 800-123 (Server Security) and SP 800-128 (Config Management)
- DISA STIGs as an alternate baseline
