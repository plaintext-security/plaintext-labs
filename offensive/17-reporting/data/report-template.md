# Penetration Test Report
<!-- Template: fill in every section; delete placeholder text before submitting -->

**Client:** Meridian Financial  
**Engagement:** Internal Web Application + Infrastructure Assessment  
**Assessment Period:** [Start Date] – [End Date]  
**Prepared by:** [Tester name / team]  
**Classification:** CONFIDENTIAL — Authorized Personnel Only  
**Version:** 1.0  

---

## Table of Contents

1. Executive Summary
2. Scope and Methodology
3. Findings Summary
4. Technical Findings
5. Remediation Roadmap
6. Appendix

---

## 1. Executive Summary

<!-- 1–2 paragraphs. Business-level language. No jargon. Answer:
     - What did we find overall? (Critical? Clean?)
     - What is the business risk? (Data breach, compliance failure, ransomware path)
     - What is the most important thing to fix first? -->

[Write a non-technical summary here. Imagine explaining this to the CFO in an elevator.
Mention the number of findings by severity, the highest-risk items, and the headline impact.]

---

## 2. Scope and Methodology

**In-scope systems:**
- [List IP ranges, hostnames, or app URLs]

**Engagement type:** [Black-box / Grey-box / White-box]

**Dates:** [Start] – [End]

**Methodology:**
1. Reconnaissance (passive and active)
2. Vulnerability identification
3. Exploitation
4. Post-exploitation
5. Reporting

**Authorization:** This assessment was conducted with written authorization from [Name/Title] at [Client].

---

## 3. Findings Summary

| ID    | Title                          | Severity | CVSS v3 | Status  |
|-------|--------------------------------|----------|---------|---------|
| F-001 | [Finding Title]                | Critical | 9.8     | Open    |
| F-002 | [Finding Title]                | High     | 7.5     | Open    |
| F-003 | [Finding Title]                | Medium   | 5.3     | Open    |
| F-004 | [Finding Title]                | Low      | 2.1     | Open    |

**Priority note:** Findings are ordered by real-world exploitability and business impact,
not raw CVSS score. F-001 is in CISA KEV and has a public exploit — address it before F-002
even though their CVSS scores are close.

---

## 4. Technical Findings

---

### F-001: [Short, specific title]

**Severity:** Critical  
**CVSS v3.1 Score:** 9.8  
**CVSS Vector:** AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H  
**CWE:** CWE-XXX — [Name]  
**Affected Asset:** [hostname / IP / endpoint]  

**Description:**
<!-- 2–3 sentences: what is the vulnerability and why does it exist? -->

**Reproduction Steps:**
```
Step 1: [command or action]
Step 2: [command or action]
Step 3: [observed result]
```

**Evidence:**
```
[Paste relevant output here — redact credentials/keys]
```
<!-- Screenshot reference: [Figure 1 — see appendix] -->

**Impact:**
<!-- Business impact: what could an attacker do with this? Data exfiltration?
     Ransomware deployment? Regulatory exposure? -->

**Remediation:**
```
[Specific fix — library version, config change, code patch]
```

**References:**
- [CVE ID if applicable — link to NVD]
- [OWASP / CWE reference]

---

<!-- Repeat the above block for each finding (F-002, F-003, ...) -->

---

## 5. Remediation Roadmap

| Priority | Finding | Remediation                    | Effort   | Owner |
|----------|---------|--------------------------------|----------|-------|
| 1 (Now)  | F-001   | [Specific action]              | 1 day    | Infra |
| 2 (30d)  | F-002   | [Specific action]              | 1 week   | Dev   |
| 3 (90d)  | F-003   | [Specific action]              | 2 days   | Ops   |

**Prioritization rationale:** [2–3 sentences explaining why this order. Reference KEV, EPSS, 
or exploitability. E.g.: "F-001 is actively exploited in the wild (CISA KEV); F-002 is
exploitable but requires authentication; F-003 is hardening rather than a direct exploit path."]

---

## 6. Appendix

### A. Scope Exclusions

[Systems explicitly out of scope and why]

### B. Tools Used

| Tool       | Version | Purpose                |
|-----------|---------|------------------------|
| nmap      | 7.94    | Port scanning          |
| nuclei    | 3.x     | Vulnerability scanning |
| [others]  |         |                        |

### C. Glossary

- **CVE** — Common Vulnerabilities and Exposures (NVD identifier)
- **CVSS** — Common Vulnerability Scoring System (0–10 severity score)
- **CISA KEV** — Known Exploited Vulnerabilities catalog (actively exploited in the wild)
- **CWE** — Common Weakness Enumeration (root-cause classification)
- **IDOR** — Insecure Direct Object Reference

### D. About This Report

This report was prepared following industry-standard penetration testing methodology
(PTES, OWASP Testing Guide). All findings were validated by the assessment team.
Findings and evidence are retained for [30/60/90] days from report delivery.
