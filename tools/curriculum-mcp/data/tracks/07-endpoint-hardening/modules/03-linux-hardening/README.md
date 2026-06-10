# Module 03 — Linux Hardening to CIS

*Module concept · [Go to the hands-on lab →](lab.md)*


**[Track 07 — Endpoint & Host Hardening]** — *Lynis and OpenSCAP scan the host and tell you exactly what to fix — the discipline is acting on the output.*

## Why this matters

Linux servers are the dominant target in cloud and on-premises data centres, and unlike Windows they have no native compliance tooling — you bring your own. OpenSCAP and Lynis are the two open-source tools that organisations actually run in production compliance programmes. Both are free, both produce machine-readable output, and both map directly to CIS Benchmarks and STIG controls. Knowing how to run them, interpret their output, and act on findings is a day-one skill for any security engineer operating in a Linux environment.

## Objective

Run Lynis and OpenSCAP against a Linux container, interpret the findings, apply a representative set of remediations, and demonstrate a measurable score improvement on the second scan.

## The core idea

Linux hardening tools split between *auditors* and *remediators*. Lynis is an auditor: it interviews the running system, outputs a scored finding list, and tells you what to do. It does not change anything itself. OpenSCAP, via the `oscap` command-line tool and the SCAP Security Guide (SSG), can both audit and remediate — the same XCCDF profile that scores the host can generate a shell script that fixes it. Understanding which tool to reach for and when is the practitioner distinction: Lynis for a quick readable score and ad-hoc forensic auditing; OpenSCAP for benchmark-mapped, policy-exportable, remediable scans in a compliance programme.

The CIS Linux Benchmarks address two categories of control: configuration settings (sysctl parameters, file permissions, service states) and installed packages (removing legacy software, ensuring security packages are present). A naive scan of a fresh OS image will score poorly on both, because default Linux installs optimise for compatibility, not security. The hardening process is iterative: scan, read the finding, decide whether to remediate or accept with justification, apply the remediation, rescan. The "accept with justification" step is not optional — a finding left open without a documented rationale is an audit liability; a finding left open *with* a documented business reason is a managed risk.

Two sysctl parameters appear on almost every CIS benchmark and illustrate the principle well. `kernel.randomize_va_space=2` enables ASLR — it makes memory layout unpredictable and significantly raises the cost of memory-corruption exploits. `net.ipv4.conf.all.accept_redirects=0` disables ICMP redirect acceptance — without this, an on-path attacker can reroute traffic through a malicious gateway. Both are one-line changes with no operational downside in almost any environment, yet both appear as findings on a default Ubuntu or RHEL install. They illustrate a wider pattern: many high-value hardening controls are trivial to apply once you know they exist.

Lynis produces a "hardening index" on a 0–100 scale. This number is useful for tracking drift over time and comparing hosts, but it is not a CIS compliance percentage — Lynis tests a broader and different set of controls than the CIS Benchmark. OpenSCAP's score *is* a CIS percentage, because it runs the official CIS XCCDF content. When you need to report to an auditor, use OpenSCAP. When you need a fast, human-readable triage of a host you've never seen before, use Lynis. In production both run, scheduled, and their output feeds a SIEM or compliance dashboard.

## Learn (~4 hrs)

**Lynis**
- [Lynis documentation — Getting Started](https://cisofy.com/documentation/lynis/get-started/) — the tool's own guide; read through the "Performing an audit" and "Understanding the report" sections (~30 min).
- [Lynis GitHub repository](https://github.com/CISOfy/lynis) — the README explains the scoring model and the output format.

**OpenSCAP and SCAP Security Guide**
- [OpenSCAP GitHub — Documentation](https://github.com/OpenSCAP/openscap/tree/maint-1.3/docs) — the tool's user guide; understand the difference between XCCDF, OVAL, and a profile scanning workflow.
- [SCAP Security Guide documentation](https://complianceascode.readthedocs.io/en/latest/) — the SSG is the content OpenSCAP scans against; read the "Profiles" section to understand how CIS, STIG, and PCI profiles differ.

**CIS Linux Benchmarks**
- [CIS Ubuntu Linux 22.04 Benchmark (free PDF)](https://www.cisecurity.org/benchmark/ubuntu_linux) — register and download; read Sections 1–2 and skim the Level 1 control list.

**Practical sysctl hardening**
- [Linux kernel hardening guide (Madaidan's Insecurities)](https://madaidans-insecurities.github.io/guides/linux-hardening.html) — a practitioner's view of kernel parameters, going beyond the CIS baseline; read the sysctl section for the "why" behind the parameters.

## Key concepts

- Lynis = auditor (reads, reports, scores); OpenSCAP = auditor + remediator (also generates fix scripts).
- CIS Benchmark controls cover two categories: configuration settings (sysctl, permissions) and package state (remove legacy software, install security packages).
- Every open finding needs either a remediation or a documented acceptance reason — undocumented open findings are audit liabilities.
- Common high-value, low-disruption controls: ASLR (`kernel.randomize_va_space=2`), ICMP redirect disable, world-writable file removal.
- Use Lynis for fast host triage; use OpenSCAP for benchmark-mapped compliance reporting.

## AI acceleration

Ask an AI assistant to explain a specific OpenSCAP finding in plain English — the XCCDF rule IDs and OVAL check descriptions are dense. The model is good at translating "xccdf_org.ssgproject.content_rule_sysctl_kernel_randomize_va_space" into "this checks that ASLR is enabled." Then verify the explanation against the SCAP Security Guide rationale for that rule. AI explains the jargon; the SSG is the authority.
