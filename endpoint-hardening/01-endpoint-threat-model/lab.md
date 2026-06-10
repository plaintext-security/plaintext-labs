# Lab 01 — Threat Model of the Endpoint

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
This is a **reference lab** — it ships a one-command environment in the companion
[`plaintext-labs`](https://github.com/plaintext-security/plaintext-labs) repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/endpoint-hardening/01-endpoint-threat-model
make demo      # print the Meridian endpoint profile and scoring rubric
```

No container is required. This is a design exercise. The `data/` directory contains
`meridian-endpoint-profile.md` — a description of a representative Meridian Financial
workstation and server — and a blank threat model template.

> No external targets. This lab produces documentation, not packets.

## Scenario

Meridian Financial has asked you to threat model two representative hosts before they begin
their CIS hardening project: a **finance analyst workstation** (Windows 11, Office 365, VPN
client, access to the financial reporting share) and a **Linux application server**
(Ubuntu 22.04, running the internal payroll API, domain-joined via SSSD). Your threat model
will drive the hardening priorities for the rest of Track 07.

## Do

1. [ ] `make demo` to read the Meridian endpoint profiles. Note the software installed, the
   network position, and the data each host holds.

2. [ ] Open `data/threat-model-template.md` and complete the **Assets** section for both
   hosts. For each asset, note its confidentiality value (low/medium/high) and its usefulness
   to an adversary (credential store, lateral movement pivot, data exfiltration target).

3. [ ] Complete the **Attack paths** section. For each asset, trace at least one realistic
   attack path using STRIDE categories. Reference the relevant ATT&CK technique IDs (e.g.
   T1003.001 for LSASS credential dumping). Keep paths grounded: phishing → code execution →
   privilege escalation → credential access is a real playbook; "attacker gains physical
   access to the data centre" is not the right threat for a laptop.

4. [ ] Complete the **Mitigations** section. For each attack path, list:
   - The CIS Benchmark control (Level 1 or 2) that closes or narrows it, or
   - The ATT&CK mitigation ID (e.g. M1026 — Privileged Account Management), or
   - A compensating control if no benchmark item applies.

5. [ ] Prioritise: rank the top five mitigations by impact (attack paths closed × asset
   value). This list becomes your hardening backlog for modules 02–06.

## Success criteria — you're done when

- [ ] Both hosts have a completed threat model with assets, paths, and mitigations.
- [ ] Every attack path references at least one ATT&CK technique ID.
- [ ] Every mitigation is mapped to a CIS control or ATT&CK mitigation.
- [ ] You have a prioritised top-five list that you can defend with reasoning.

## Deliverables

`threat-model.md` — your completed threat model for both Meridian hosts. Commit it to your
portfolio repo. This document drives the rest of the track.

## Automate & own it

**Required.** Write a short Python or shell script (`score_threat_model.py`) that reads your
threat model Markdown and counts: number of assets enumerated, number of attack paths, number
of mitigations with a CIS control ID, and number of mitigations with an ATT&CK ID. Output a
one-line coverage summary. Have an AI draft the parser; you review each line and verify the
counts are correct before committing.

## AI acceleration

Ask an AI to generate a STRIDE analysis for the finance analyst workstation role. Use its
output as a *starting point* — then challenge every threat: is this technique observed in the
wild against this OS? Does Meridian's specific software stack change the exposure? Add the
organisation-specific paths (payroll API access, VPN split-tunnel, domain join) that the
model can't infer. The model drafts the shape; you fill in what it can't know.

## Connects forward

The threat model's top-five list becomes the hardening backlog for module 02 (Windows) and
module 03 (Linux). Module 09 (privilege-escalation defense) extends the "Elevation of
Privilege" paths you identified here. Module 10 (detecting host compromise) maps detections
to each attack path — so a well-structured threat model makes module 10 much faster.

## Marketable proof

> "I threat-modelled a mixed Windows/Linux endpoint estate — assets, ATT&CK-mapped attack
> paths, and a prioritised control backlog — before writing a single hardening rule."

## Stretch

- Map your top five mitigations to the CIS Controls v8 IG1 list. Are all five in IG1, or did
  your threat model surface something that basic hygiene alone doesn't cover?
- Add a "residual risk" column to the mitigations table — what does the adversary still have
  available after each control is applied?
