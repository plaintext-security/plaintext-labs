# Module 08 — Path to Domain Admin

*Type 6 · Reconstruct — chain modules 02–07 into one walked, narrated `jsmith → Domain Admins` path on the Corp BloodHound dataset, mapping each hop to its ATT&CK technique and the artefact it leaves, delivering a client-actionable written attack-path report (the phase project). (Secondary: Blast-Radius Trace — quantify the reach exposed at each hop along the chain.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Active Directory & Windows Security** — *the skill is not running the tools — it is reading the graph and writing the narrative.*

<!-- module-meta -->
**Difficulty:** Advanced &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters

A penetration tester who runs BloodHound and hands over the raw JSON hasn't done the hard part. The hard part is translating a graph of hundreds of edges into a prioritised, walked, documented attack path: this is the hop, this is the technique, this is the artefact, this is what you must fix first. This module is where all the individual techniques from modules 02-07 come together into a single, coherent end-to-end path — and where the skill of synthesis becomes as important as the skill of execution.

## Objective

Given the pre-generated BloodHound attack-path dataset for Corp, trace the complete multi-hop path from `jsmith` to `Domain Admins`, map each hop to its ATT&CK technique, document the artefact each hop leaves, and produce a written attack path report a client could act on.

## The core idea

A BloodHound graph of a real domain can have thousands of nodes and tens of thousands of edges. The graph query "Shortest Paths from Domain Users to Domain Admins" often returns dozens of paths — and most real-world engagements find the path is not through a single clever exploit but through a chain of mundane misconfigurations that individually look harmless. The synthesis challenge is to pick the *most realistic* path (not just the shortest), because real attackers choose paths based on operational constraints: which credentials do I already have? Which hosts can I reach from here? Which technique is less likely to trigger an alert?

Reading a BloodHound graph well requires internalising what each edge type means operationally. The practitioner translation: the graph is a road map and **each edge is a road with its own toll, speed limit, and traffic camera** — BloodHound draws them all the same width, but they are not equal. `MemberOf` is free — it requires no action. `GenericWrite` on a group requires one LDAP write operation. `AdminTo` means local admin via PTH or Kerberos. `HasSession` means a privileged user's credential is cached in memory on a reachable host — one of the most valuable edges because it converts host access directly into a new credential. `CanPSRemote` means WinRM execution. Each edge has an approximate noise level, a required precondition, and a resulting access level. A practitioner reads the graph and chooses the path that minimises noise and maximises reach — and knows that an edge BloodHound *shows* may still be a dead end on the day, because the session it relied on has logged off or the precondition no longer holds. The graph is a hypothesis to walk, not a guarantee.

The deliverable that matters is the **attack path narrative**: not a screenshot of BloodHound, but a written step-by-step chain that answers the question "how did they get from Finance workstation to Domain Admin without triggering a single alert?" Each step names the technique, the credential, the specific system action, and the event it generates (or doesn't). This is the document that drives prioritisation: the client fixes the highest-impact misconfiguration first — the one that breaks the most paths — not the one at the end of the chain.

The closing exercise — mapping mitigations — is where the red and blue perspectives converge. For each hop in the path, you identify the specific control that breaks it: rotate service account passwords (breaks Kerberoast), require SMB signing (breaks relay), remove GenericWrite ACE (breaks group manipulation), deploy LAPS (breaks local admin PTH). A mature engagement delivers not just "here's the path" but "here's the path, here's the hop-by-hop mitigation priority, and here's the projected posture after each fix."

## Learn (~3 hrs)

**BloodHound path analysis**
- [BloodHound CE — Cypher query reference (GitHub)](https://github.com/SpecterOps/BloodHound/wiki) — the canonical query reference. The most important query: `MATCH p=shortestPath((u:User {name:'JSMITH@CORP.LOCAL'})-[*1..]->(g:Group {name:'DOMAIN ADMINS@CORP.LOCAL'})) RETURN p`.

**ATT&CK mapping**
- [MITRE ATT&CK — Enterprise matrix, Credential Access + Lateral Movement](https://attack.mitre.org/matrices/enterprise/) — review the full matrix for Windows; every hop in the Corp path maps to a technique here. Know the sub-technique IDs.

**Report writing**
- [SpecterOps — How to Write an AD Assessment Report (blog)](https://posts.specterops.io/attack-path-analysis-for-defenders-part-1-665f0e8a4c72) — the defenders' framing of attack path analysis; explains how to translate a BloodHound graph into a prioritised client deliverable.

## Key concepts
- The most realistic path is not always the shortest — it is the one a real attacker would choose given their constraints.
- Edge types have different operational cost and noise levels: `MemberOf` = free; `GenericWrite` = one LDAP write; `HasSession` = PTH on a live host.
- The attack path narrative maps each hop to: technique, credential, action, event generated.
- Mitigation priority = break the chain at the hop that disrupts the most paths (often an ACL fix or service account rotation, not a DA password change).
- A complete engagement deliverable: the path + the hop-by-hop fix + the projected posture change after each fix.

## AI acceleration

Paste the attack path JSON into a model and ask it to write the client-facing narrative — plain English, no jargon, one paragraph per hop. The model does this well. Your job is to verify: does the model describe the technique accurately? Does it correctly name which event is generated (or not)? Does it identify the correct mitigation? Have the model draft, then fact-check each claim against the ATT&CK page for that technique.
