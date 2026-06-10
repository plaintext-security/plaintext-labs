# Module 13 — Incident Response Process

*Module concept · [Go to the hands-on lab →](lab.md)*


**Digital Forensics & IR** — *the investigation without a process is just a fire drill — the process is what turns technical findings into organisational decisions.*

## Why this matters

Technical forensic skill without a process framework produces findings that go nowhere. A
responder who can identify timestomping, reconstruct a CloudTrail attack chain, and profile a
dropper with CAPA — but who doesn't know when to escalate, who to notify, how to document
decisions, or what "eradication" means in their environment — is a technician, not a responder.
NIST SP 800-61 is the process skeleton that most IR programs in regulated industries are built
on; knowing it means knowing how to operate in any of them.

## Objective

Map the Meridian Financial incident to the four phases of NIST SP 800-61, identify gaps and
successes in the simulated response, and produce a structured post-incident analysis that a
security manager or auditor could use.

## The core idea

NIST SP 800-61 structures incident response into four phases: **Preparation, Detection &
Analysis, Containment/Eradication/Recovery, and Post-Incident Activity.** These are not
sequential in practice — a real response cycles between Detection and Containment many times as
new hosts are scoped in — but as an analytical frame, they give you a consistent way to audit
any incident response: what did the team know and when, what decisions were made, what was
contained and when, and what was learned.

The phase that responders most consistently execute poorly is **Containment**, and the failure
mode is almost always one of two things: containing too early (before scoping is complete, so
the attacker pivots to a host you haven't identified yet) or containing too late (waiting for
forensic certainty before acting, while the attacker continues to operate). The decision is
never "do we have enough evidence?" — it's "does the evidence we have change the cost-benefit
of waiting?" A live attacker with persistence on two hosts is a different calculation than a
months-old compromised account with no evidence of recent activity. **Containment is a
business decision informed by technical findings, not a technical decision.**

**Eradication** is the phase most organisations underestimate in complexity. Identifying and
removing the backdoor is the obvious step; equally important are: rotating all credentials
that touched the compromised host or used by the compromised account, revoking and reissuing
any secrets or certificates the host had access to, auditing all systems the compromised account
could reach, and confirming that the initial access vector is closed. An eradication that misses
the AWS access key that was exfiltrated and used to create a backdoor IAM user — as in the
Meridian case — is not eradication. It's cleanup theater.

**Post-Incident Activity** is where institutional learning happens, and most teams do it
badly or not at all. A post-incident review that is only a timeline ("what happened") instead
of a causal analysis ("why did this happen and what would have stopped it") produces a report
but not an improvement. The two questions worth forcing: "what was the first detection that
*could* have fired, and why didn't it?" and "what single control, if implemented, would have
had the highest probability of stopping or detecting this earlier?" Those two answers drive the
remediation roadmap more than any checklist.

## Learn (~2 hrs)

**NIST SP 800-61 (~1 hr)**
- [NIST SP 800-61 Rev. 2 — Computer Security Incident Handling Guide (PDF)](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r2.pdf) — the canonical reference. Read Sections 3 (Handling an Incident) and 4 (Coordination and Information Sharing) — about 40 pages, but dense with practical guidance. This is the specification the lab exercise maps to.
- [CISA — Incident Response Playbook (PDF)](https://www.cisa.gov/sites/default/files/2024-08/Federal_Government_Cybersecurity_Incident_and_Vulnerability_Response_Playbooks_508C.pdf) — CISA's operationalised playbook that implements NIST 800-61 for federal agencies; readable as a concrete example of what the framework looks like in practice.

**IR in practice (~0.5 hrs)**
- [SANS — The Incident Handler's Handbook (PDF)](https://www.sans.org/white-papers/33901/) — a free practitioner walkthrough of the NIST phases with real-world colour on where responses go wrong. Read sections 2 and 3 for the triage and containment decision frameworks.

**Post-incident analysis (~0.5 hrs)**

## Key concepts
- NIST SP 800-61 phases: Preparation → Detection & Analysis → Containment/Eradication/Recovery → Post-Incident
- Containment timing: a business decision (cost of waiting vs. cost of acting) informed by technical scope
- Eradication completeness: backdoors, credentials, secrets, access vectors — all must be addressed
- Post-incident review quality: causal analysis ("why did controls fail?") beats timeline ("what happened?")
- Evidence tracking: chain of custody, decision log, and notification record are non-optional in regulated industries
- The "lessons learned" artifact is an organisational deliverable, not an optional appendix

## AI acceleration

The synthesis task in post-incident review — reading a long timeline, identifying causal factors,
and drafting remediation recommendations — is well-suited to AI assistance. Feed the merged
incident timeline (from module 10) to a model and ask: "What was the earliest point this incident
could have been detected? What controls, if present, would have stopped it?" Use the model's output
as a starting point; the output must be reviewed against your actual environment and organisational
context. A model answering from a generic knowledge base will recommend controls you may already
have and miss gaps specific to your configuration. The review judgment is yours.
