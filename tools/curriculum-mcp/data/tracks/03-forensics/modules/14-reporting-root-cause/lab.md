# Lab 14 — Reporting & Root-Cause Analysis

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This is a **concept and writing module** — no container required. The exercise materials are in
the companion [`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/forensics/14-reporting-root-cause
make demo    # prints the grading rubric and instructions
```

Open:
- `data/report-template.md` — the forensic incident report template with all required sections.
- `data/meridian-findings.md` — the raw forensic findings from the Meridian investigation
  (the "notes before the report").

Your task: write the report by filling in the template from the findings.

> This exercise produces a training artifact. Do not submit findings from real incidents
> as portfolio work without organisational approval and appropriate anonymisation.

## Scenario

The Meridian Financial incident is closed. You are writing the final forensic incident report,
which will be delivered to: (1) the CISO and CFO (executive audience), (2) the IT security team
(technical audience), and (3) outside legal counsel (legal and compliance audience). All three
audiences will read the same document. Your report must serve all three.

## Do

1. [ ] **Read `data/meridian-findings.md` in full.** Identify which findings are:
   - Confirmed (direct artifact evidence)
   - Inferred (reasonable conclusion from multiple artifacts, but not directly observed)
   - Possible but unconfirmed (attacker capability without artifact-based confirmation)

   Label each finding in the margins before writing — this discipline prevents scope overstatement.

2. [ ] **Write the Executive Summary.** Using the template section, write three paragraphs:
   - Paragraph 1: what happened and when (no jargon, no field names, no Event IDs).
   - Paragraph 2: scope — what was confirmed as compromised, and what was exposed but not confirmed.
   - Paragraph 3: the three highest-priority remediation actions.
   
   Stay under 250 words. Test it: would a CFO who doesn't know what a scheduled task is
   understand this completely?

3. [ ] **Write the Technical Findings section.** For each finding, format it as:
   ```
   Finding [N]: [Name]
   Evidence: [Artifact name] → [Field] = [Value] (e.g., Hayabusa triage → EventID=4698, 
   TaskName=\MicrosoftEdgeUpdateTaskUser, Timestamp=2024-03-15T14:18:03Z)
   ATT&CK: [Technique ID] — [Technique Name]
   ```
   Include at least six findings, each with artifact citation and ATT&CK mapping.

4. [ ] **Write the Root-Cause Analysis.** Apply the 5 Whys to the phishing bypass:
   - Why did the incident succeed? → Because the phishing email delivered a malicious attachment.
   - Why did the attachment execute? → Because...
   - Continue until you reach a control gap the organisation could address.
   
   State the root cause as: "The root cause is [X] because [it is the earliest point in the
   causal chain at which an available control could have stopped the incident]."

5. [ ] **Complete the IOC table.** The template includes an IOC table with columns: Type,
   Value, Confidence, First Seen, Last Seen, Source Artifact. Fill it in for all IOCs identified
   across modules 08–12 (IP address, domain, file hash, file path, IAM username).

6. [ ] **Run the linting script:**
   ```bash
   python3 scripts/lint_report.py your-report.md
   ```
   Fix any structural issues it flags before finalising.

## Success criteria — you're done when

- [ ] Executive Summary is complete (under 250 words, jargon-free, scope accurately hedged).
- [ ] Technical Findings section has at least six artifact-cited findings with ATT&CK mappings.
- [ ] Root-cause analysis identifies a specific control gap, not a human behaviour.
- [ ] IOC table is populated with at least five IOCs from the Meridian investigation.
- [ ] `lint_report.py` reports zero structural issues.

## Deliverables

Commit to your portfolio repo:
- `meridian-incident-report.md` — the completed report using the template.
- `scripts/lint_report.py` — the linting script (from the lab, extended if desired).

This is your capstone-adjacent deliverable — a portfolio-ready forensic report that demonstrates
end-to-end IR capability from detection through written finding.

## Automate & own it

**Required.** Extend `lint_report.py` (provided in the lab) to additionally check:
1. Every entry in the Technical Findings section has at least one artifact citation in the
   format `[Artifact] → [Field] = [Value]`.
2. The IOC table has at least one row per IOC type (IP, Domain, File Hash, Path, User).
3. The Executive Summary is under 300 words.
4. Output a pass/fail result with specific line-number references for each failure.

Have a model draft the extensions; **run it against a deliberately broken version of the report**
(remove a section, empty the IOC table) to confirm it catches the failures before using it to
validate your own report. Commit the extended version.

## AI acceleration

Generate the first draft of the Executive Summary by prompting: "Write a 3-paragraph executive
summary for a CISO and CFO with no technical background, based on these findings: [paste findings
list]." Then edit for accuracy: check every claim against the confirmed-vs-inferred labels from
step 1. The model will likely overstate certainty ("the attacker exfiltrated data") where the
correct statement is "the attacker had access to data with no confirmed evidence of exfiltration."
That edit — changing an assertion to a characterisation of exposure — is the most important
report-writing skill, and it requires you, not the model.

## Connects forward

This report format is the deliverable in the Track 03 capstone: take a training disk image
through acquisition, timeline, and root-cause analysis, and produce a report using this template.
The report is also the portfolio artifact that demonstrates end-to-end IR competency in job
applications and technical interviews.

## Marketable proof

> "I write forensic incident reports that serve executive, technical, and legal audiences
> simultaneously — with artifact-cited findings, a root-cause analysis that identifies specific
> control gaps, and remediation priorities a CISO can take to a board."

## Stretch

- Submit your report draft to a model and ask it to act as a "hostile expert witness" reviewing
  the report for assertions that overstate certainty, missing artifact citations, or scope
  language that could be challenged in a legal proceeding. Revise based on the critique and
  document what changed and why.
- Add a "Detection Coverage Analysis" appendix: for each ATT&CK technique identified in the
  report, state whether Meridian had a detection in place at the time, whether it fired, and
  whether it *could* have fired with reasonable configuration. This appendix directly drives
  the detection improvement roadmap.
