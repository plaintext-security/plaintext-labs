# Module 14 — Reporting & Root-Cause Analysis

*Module concept · [Go to the hands-on lab →](lab.md)*


**Digital Forensics & IR** — *the investigation is only as valuable as the report — findings that can't survive scrutiny, or can't be read by a non-technical audience, don't drive decisions.*

## Why this matters

Every forensic finding, every log artifact, every capability profile is only useful if it ends up
in a report that a) survives technical scrutiny and b) reaches the people who need to act on it.
A timeline that only a forensicator can read doesn't get the CISO to approve the remediation
budget. A report that executives can read but investigators can't reproduce doesn't hold up in a
regulatory review or legal proceeding. Writing the report — and particularly the root-cause
analysis — is the skill that determines whether the investigation was worth doing.

## Objective

Write a forensic incident report for the Meridian Financial incident using the provided template
and raw findings, with a root-cause analysis that distinguishes contributing causes from the
root cause, and run the structural linting script to confirm all required sections are present
and populated.

## The core idea

Forensic reports serve multiple audiences simultaneously, and most reports fail because they pick
one. The executive audience needs to understand what happened, what it cost, and what to do about
it — in three paragraphs. The technical audience needs to be able to reproduce every finding from
the artifacts cited. The legal and compliance audience needs a clear chain of custody, accurate
scope language, and findings that are stated as facts ("the file existed at path X at time Y,
as evidenced by artifact Z") rather than inferences presented as facts. A report that serves all
three audiences uses a layered structure: Executive Summary (three paragraphs), Technical Findings
(artifact-cited, reproducible), and Appendix (raw evidence, tool output, methodology notes).

Root-cause analysis is the part most IR reports skip or do badly. The common mistake is to stop
at the proximate cause: "the developer clicked a phishing link." That is true but useless — it
implies the remediation is "don't click phishing links," which is not a security control. A proper
root-cause analysis asks why each contributing factor existed. Why did the phishing email bypass
the gateway? Because DMARC was in reporting-only mode, not enforcement. Why did macro execution
succeed? Because the endpoint's Office configuration didn't disable macros from internet-origin
documents. Why did the attacker reach the C2 IP? Because the egress firewall allowed outbound
HTTP from workstations. Each of these is an actionable finding; the root cause is the earliest
in the causal chain that the organisation could have reasonably addressed. **Root cause is not the
first thing that went wrong; it's the last place a control could have stopped the chain.**

The other trap in forensic reports is scope language: "the attacker had access to all systems
accessible from the compromised account" is a finding. "The attacker accessed all those systems"
is an overstatement unless you have artifact evidence of each access. Report what you can prove
from artifacts; characterise the *exposure* (what was reachable) separately from confirmed access.
Legal proceedings and regulatory submissions are where imprecise scope language creates liability —
a report that overstates access in an IR report is a legal problem, not just an accuracy problem.

The final element that separates useful reports from documentation exercises is the **remediation
section**, and specifically the prioritisation within it. A list of forty recommendations is not
actionable; a prioritised short list of the three to five controls that break the attack chain, with
effort estimates, is what a CISO can take to a board. Write the remediation section as if budget is
constrained — because it always is — and prioritise by: (1) closes the initial access vector,
(2) reduces dwell time on the next similar incident, (3) improves future detection or investigation.

## Learn (~2 hrs)

**Forensic report writing (~1 hr)**
- [NIST SP 800-86: Guide to Integrating Forensic Techniques into Incident Response](https://csrc.nist.gov/pubs/sp/800/86/final) — the U.S. government standard for forensic documentation and reporting; sections 5–6 cover report structure, findings documentation, and defensible conclusions. Free PDF.

**Root-cause analysis (~0.5 hrs)**
- [NIST SP 800-61 Rev. 2 — Section 3.4: Post-Incident Activity](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf) — the NIST guidance on lessons-learned meetings and the questions to drive toward root cause. Focus on section 3.4.1 — "Lessons Learned."
- [The "5 Whys" technique](https://en.wikipedia.org/wiki/Five_whys) — the standard structured approach to drilling past proximate causes to root cause. Apply it to the phishing-gateway bypass in the Meridian case as a warm-up.

**Legal and evidence considerations (~0.5 hrs)**

## Key concepts
- Layered report structure: Executive Summary → Technical Findings → Appendix
- Executive summary: what happened, what it cost, what to do — three paragraphs
- Technical findings: every claim cited to a specific artifact, field, and value
- Root cause ≠ proximate cause: root cause is the last control that could have stopped the chain
- Scope language: distinguish confirmed access (evidenced) from exposure (reachable but not confirmed)
- Remediation prioritisation: break the access vector, reduce dwell time, improve detection — in order
- Report linting: structural completeness (all sections present, IOC table populated) is a minimum bar

## AI acceleration

An AI model is an excellent first-draft generator for executive summaries: give it the technical
findings in bullet form and ask for a three-paragraph executive summary at "CISO level." The model
will produce coherent prose, but will often overstate certainty ("the attacker accessed production
data" rather than "the attacker had access to production data with no evidence of confirmed access").
Read every sentence in the generated summary against the technical findings: any assertion not
traceable to a specific artifact must be either removed or downgraded to an appropriately hedged
characterisation. The model drafts the structure; you edit for accuracy and defensibility.
