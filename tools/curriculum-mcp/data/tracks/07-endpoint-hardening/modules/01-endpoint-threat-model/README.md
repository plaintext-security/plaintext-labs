# Module 01 — Threat Model of the Endpoint

*Module concept · [Go to the hands-on lab →](lab.md)*


**[Track 07 — Endpoint & Host Hardening]** — *Before you harden anything, decide what you're actually defending it from.*

## Why this matters

Every hardening checklist was written for a generic "enterprise workstation." Your endpoint is not generic — it runs specific software, holds specific data, and sits in a specific network position. Applying a 300-item benchmark without understanding which 30 items actually matter for your threat model is how teams burn time patching theoretical risks while leaving real ones open. The threat model comes first because it determines which controls get prioritised, which can be deferred, and which benchmarks are the right starting point at all.

## Objective

Produce a threat model for a representative Meridian Financial endpoint — identifying the assets on the host, the realistic adversary objectives, the attack paths that reach them, and the mitigations (already present and recommended) mapped to each path.

## The core idea

An endpoint threat model is a structured conversation about attacker economics. The host is not uniformly valuable — the threat model asks *what is on this machine that an adversary would want*, *how would they reach it from their likely entry point*, and *what is the cheapest control that closes or significantly narrows that path*. Most attackers are not targeting your specific company; they are running playbooks against the class of target you represent. The threat model's first job is to figure out which playbook.

The STRIDE model (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) is a useful lens for endpoints even though it was designed for applications. A workstation can be spoofed (credential theft lets an adversary impersonate the user), tampered with (a rootkit modifies the kernel or audit logs), and elevated against (a local privilege-escalation exploit moves the adversary from user to SYSTEM). Running STRIDE systematically prevents the "we only thought about malware" failure where teams harden against commodity threats but overlook the post-exploitation phase that actually causes breach impact.

Assets on an endpoint are rarely just files. They include cached credentials (LSASS memory, browser-saved passwords, SSH agent, token caches), access context (what network segments and cloud resources this machine can reach), software supply chain risk (the developer laptop that can push to prod is a higher-value target than the lobby kiosk), and the host's position in the domain (a machine that can enroll new certificates or modify group policy is a domain takeover asset). The threat model must enumerate all of these — not just the sensitive documents in the user's home directory.

Mitigations follow from the asset/path analysis. A control that doesn't close or narrow an attack path — even if it appears on the CIS benchmark — is low priority. A control that is not on the benchmark but does close a high-value path goes on the model anyway. The output of a good endpoint threat model is a prioritised list of controls, not a compliance score. Compliance scoring is the *measurement* of whether you implemented the controls; the threat model is what tells you which controls to implement.

## Learn (~3 hrs)

**Threat modelling fundamentals**
- [Threat Modeling: Designing for Security (Adam Shostack, Chapter 1 excerpt)](https://www.oreilly.com/library/view/threat-modeling/9781118810057/) — the originator's framing; read Chapter 1 for the four-question framework (what, find, do, check).
- [OWASP Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html) — concise reference for the process; skim the full page (~20 min) to map STRIDE to concrete attack categories.

**Endpoint-specific threat landscape**
- [MITRE ATT&CK Enterprise — Initial Access & Execution](https://attack.mitre.org/matrices/enterprise/) — the adversary playbook; focus on the Initial Access and Execution columns to understand how attackers reach and use an endpoint.
- [CIS Controls v8 — Implementation Group 1](https://www.cisecurity.org/controls/v8) — the "essential hygiene" baseline; read the IG1 summary (free PDF, ~10 pages) to see which controls a small team prioritises first.

**Credential theft on the endpoint**
- [Credential Access — MITRE ATT&CK (TA0006)](https://attack.mitre.org/tactics/TA0006/) — the single most-abused post-compromise tactic; read the technique list and pick three that apply to your target environment.

## Key concepts

- Threat modelling answers four questions: what are we building, what can go wrong, what do we do about it, did we do a good job.
- STRIDE categories map to concrete endpoint attacks: Elevation of Privilege → local privesc; Tampering → rootkits and log manipulation; Information Disclosure → credential dumping.
- Endpoint assets include cached credentials and access context, not just files.
- Controls should be prioritised by how many attack paths they close, not by benchmark item number.
- A compliance score measures implementation; the threat model determines *which* controls to implement.

## AI acceleration

Use an AI assistant to enumerate attack paths you might have missed — describe the endpoint's role (developer workstation, finance user, build server) and ask it to generate a STRIDE analysis for that role. Then *validate each threat* against ATT&CK: does the technique exist, is it commonly observed in the wild, does it apply to your OS version? AI is fast at generating lists; your job is to prune the implausible ones and add the organisation-specific ones it can't know.
