# Module 07 — Compliance Scoring & Auditing

*Module concept · [Go to the hands-on lab →](lab.md)*


**[Track 07 — Endpoint & Host Hardening]** — *A compliance score you run once is a photograph; a score you run on a schedule is a vital sign.*

## Why this matters

Every compliance framework — PCI-DSS, HIPAA, SOC 2, ISO 27001 — requires evidence that security controls are continuously applied, not just checked during an annual audit. Compliance scoring tools turn the hardening work of modules 02–06 into measurable, reportable evidence. The discipline of running them on a schedule, tracking the score over time, and treating a score drop as an incident is what separates organisations that are compliant from organisations that *check* compliant.

## Objective

Run OpenSCAP and Lynis against a deliberately un-hardened container, apply one targeted fix, and demonstrate a measurable before/after delta — practicing the audit-remediate-verify cycle that is the operational heartbeat of a compliance programme.

## The core idea

Compliance auditing and security hardening are related but distinct activities. Hardening is the engineering work of applying controls; compliance auditing is the measurement work of verifying those controls are in place and producing evidence for auditors. The measurement tools (OpenSCAP, Lynis, CIS-CAT) don't know if you're secure — they know if specific, pre-defined controls are in a specific state. A host can score 95% on CIS Level 1 and still be trivially exploitable through a misconfiguration the benchmark doesn't cover. Understanding this gap is the practitioner calibration: use compliance scoring as a systematic check on your hardening baseline, not as a security oracle.

The before/after scoring cycle is the fundamental unit of work. Before you apply a control, capture the baseline score. Apply the control. Rescan and capture the after score. The delta is your evidence: this control changed the score from X% to Y%, and here are the specific CIS rule IDs that moved from fail to pass. This is what an auditor reviews, not the fact that you ran a script. The structured output — OpenSCAP XML, Lynis log, CIS-CAT JSON — is the evidence chain. Treat it as an audit artefact: version-control it, timestamp it, and never edit it after generation.

Exception management is the part of compliance auditing that organisations get wrong most often. No benchmark is 100% applicable to every environment — containers can't set certain kernel parameters, legacy applications require deprecated cipher suites, operational requirements override a control's default. An open finding with no documentation is an audit liability. The same finding with a documented risk acceptance ("Control X.Y.Z cannot be applied because of constraint Z; risk accepted by security lead on YYYY-MM-DD; mitigated by compensating control W") is a managed exception. The compliance programme requires a formal exception process, not a perfect score.

Continuous compliance — running scans on a schedule and alerting on score drift — is the operational maturity that separates a compliance programme from a pre-audit scramble. The implementation is straightforward: a cron job or CI pipeline that runs the scan, compares the score to the previous baseline, and pages if the score drops more than a threshold. The cultural change it requires is treating a compliance score drop the same way you treat an alert: investigate, identify the change that caused it, and either remediate or document an exception. This turns compliance from a once-a-year event into an operational practice.

## Learn (~3 hrs)

**Compliance frameworks and tools**
- [PCI-DSS v4.0 — Section 2 (System Components Configuration)](https://www.pcisecuritystandards.org/document_library/) — free download; read Section 2 to understand what a compliance framework actually demands from a hardening programme.
- [NIST SP 800-128 — Guide for Security-Focused Configuration Management](https://csrc.nist.gov/pubs/sp/800/128/upd1/final) — Sections 2–3 give the framework for continuous compliance as a lifecycle process.

**OpenSCAP and Lynis (review from module 03)**
- [OpenSCAP GitHub — User Guide and Report Generation](https://github.com/OpenSCAP/openscap/tree/maint-1.3/docs) — specifically the report format documentation; HTML and XCCDF are the audit evidence formats used for compliance scoring.
- [Lynis CI integration guide (CISOfy)](https://cisofy.com/documentation/lynis/get-started/#cicd) — running Lynis in CI; read for the exit-code and threshold patterns.

**Continuous compliance**
- [SCAP workbench (OpenSCAP GUI)](https://www.open-scap.org/tools/scap-workbench/) — a point-and-click interface for running SCAP scans; useful for understanding the report before scripting it.

## Key concepts

- Compliance scoring measures whether specific controls are applied; it is not a security oracle.
- Before/after scoring is the evidence chain: structured output, timestamped, version-controlled.
- Exception management: every open finding needs either a remediation or a documented risk acceptance.
- Continuous compliance = scheduled scans + score-drift alerting = compliance as an operational practice.
- OpenSCAP XML output is the auditor's artefact; Lynis log is the analyst's triage tool.

## AI acceleration

Ask an AI to explain a failing OpenSCAP rule's OVAL definition in plain English — the XCCDF/OVAL XML is dense and hard to read. Use the explanation to understand what state the rule is actually testing, then verify against the CIS benchmark rationale. AI is a good XCCDF translator; the benchmark is the authority on whether the translation is correct.
