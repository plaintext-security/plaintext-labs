# Lab 17 — Penetration Test Reporting

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs.git
cd plaintext-labs/offensive/17-reporting
make demo   # prints writing guide, validates template, checks reference URLs
```

No Docker required. The validator and report template run with Python 3 only.

## Scenario

You have completed a simulated penetration test against Meridian Financial's
internal web application. Your raw notes include findings from throughout the
offensive track (SSRF, IDOR, privilege escalation, LOLBins). Turn those raw
notes into a professional deliverable the CISO can share with the board and
the engineering team can act on within 30 days.

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Do

1. [ ] Run `make demo`. Observe:
   - Which 11 structural sections the validator checks for.
   - The five common writing mistakes and their fixes.
   - The public report references (confirm they resolve with ✓).

2. [ ] Copy the template and start filling it in:
   ```bash
   cp data/report-template.md engagement-report.md
   ```
   Use findings from this track (modules 07–14). Include at least three findings
   across Critical, High, and Medium severity.

3. [ ] For each finding, complete all fields:
   - **Severity + CVSS 3.1 vector** (use the calculator at first.org/cvss)
   - **CWE** (look up at cwe.mitre.org)
   - **Reproduction steps** (specific commands from your lab notes)
   - **Impact** in business terms (what could an attacker do with this?)
   - **Remediation** specific enough to assign to a developer

4. [ ] Write the Executive Summary. Rules:
   - No acronyms without expansion on first use.
   - State total findings by severity.
   - State the business risk in one sentence.
   - Name no specific vulnerabilities (that belongs in section 4).

5. [ ] Validate your report:
   ```bash
   make validate FILE=engagement-report.md
   ```
   Fix any ✗ marks until 11/11 pass.

6. [ ] Read two public reports from the references printed by `make demo`. For each:
   - How does their executive summary differ from yours?
   - What evidence do they include per finding?
   - How specific are their remediation recommendations?

## Success criteria — you're done when

- [ ] `make validate FILE=engagement-report.md` passes 11/11 checks.
- [ ] Executive Summary reads cleanly to a non-technical reader.
- [ ] Every finding has CVSS, CWE, reproduction steps, impact, and remediation.
- [ ] Remediation roadmap orders findings by real-world exploitability, not raw CVSS.

## Deliverables

Commit `engagement-report.md`. This is a portfolio piece — it demonstrates not
just technical skill but the written communication that clients pay for.

> **Artifact hygiene:** Do not commit screenshots, pcap files, or evidence dumps —
> reference them as "[Figure 1 — see appendix]" and keep the originals local.

## Automate & own it

**Required.** Write `gen_finding.py` that:
- Takes `--title`, `--severity`, `--cvss`, `--cwe`, `--desc`, `--repro`, `--impact`,
  `--remediation` as arguments
- Outputs a correctly-formatted finding block (Markdown) matching the report template
- Can be called in a loop over a findings JSON file

AI drafts it; you verify the field ordering matches the template exactly, then run it
against your three findings. Commit `gen_finding.py`.

## AI acceleration

Paste your raw lab notes (terminal output, vulnerability description) into a model
and ask it to draft the finding block. Then review every sentence:
- Does the CVSS vector match the actual attack path?
- Is the impact overstated or vague?
- Is the remediation actionable, or is it "sanitize inputs"?

The skill is in the review, not the generation.

## Connects forward

This is the capstone of Track 01 — every specialization track ends in a deliverable,
and the report format (clear, evidence-backed, actionable) carries into all of them.
The defensive tracks also consume this format: a SOC analyst reviewing a pentest
report reads CVSS, reproduction steps, and indicators of compromise to build
detection logic.

## Marketable proof

> "I write professional pentest reports: executive summary, CVSS-scored technical
> findings, risk-based prioritisation, and actionable remediation — modeled on real
> industry reports. I can validate report completeness programmatically."

## Stretch

- Validate one of the public Cure53 reports with `python3 validate.py <file>`. Does it
  pass 11/11? What structural differences do you see?
- Add a severity-distribution bar chart (ASCII) to `validate.py` that counts
  Critical/High/Medium/Low findings in the report under test.
- Stand up Ghostwriter and produce the same report through it, to see how consultancies
  manage findings at scale.
