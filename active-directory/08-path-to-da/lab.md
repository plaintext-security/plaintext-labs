# Lab 08 — Path to Domain Admin

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

You collect the graph **for real** from the live Samba DC, then analyse it offline.

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/active-directory/08-path-to-da
make up       # start the Samba DC + a bloodhound-python collector
make collect  # run a LIVE BloodHound collection against dc01.corp.local (writes data/*.zip)
make demo     # analyse the attack paths with ATT&CK mapping
make down
```

`make collect` runs `bloodhound-python` as `jsmith` against the DC over real LDAP/SMB and drops the SharpHound-format JSON (zipped) into `data/`. Import that zip into BloodHound CE (Docker — see the [official quick start](https://github.com/SpecterOps/BloodHound#quick-start)) to walk the graph visually. The curated `data/bloodhound-attack-paths.json` is a *reference* dataset: a worked, fully annotated path with ATT&CK metadata that `path-analyzer.py` reads, so you have a canonical answer to check your own analysis against.

> Authorization: this collector talks to the DC that ships with this lab — it's yours, collect freely. The habit holds everywhere else: only run BloodHound against domains you own or are authorised to assess.

## Scenario

You are completing a red team engagement for Corp. You have reached the end of the active exploitation phase and have domain admin access. Your deliverable to the client is a complete attack path report: the chain from `jsmith` to `Domain Admins`, each hop explained and mapped to ATT&CK, with prioritised mitigations. This is the document that drives the client's remediation roadmap.

## Do

1. [ ] **Collect the live graph, then load the reference path.** Run `make collect` to pull the real graph off `dc01.corp.local` — note which objects, edges, and SPNs the collector actually found (this is *your* data, not a fixture). Then run `make demo` to see the curated reference path printed with ATT&CK technique IDs, open `data/bloodhound-attack-paths.json`, and understand the schema: nodes, edges, hop metadata. Confirm the accounts in the reference path (svc-mssql, svc-deploy, IT-Admins, …) are the ones your live collection surfaced.

2. [ ] **Trace each hop.** For each hop in the path, answer in writing:
   - What is the starting credential and how was it obtained?
   - What specific action does the attacker perform?
   - What system resource is accessed (which host, which service, which protocol)?
   - What Windows Event ID is generated on the target, if any?
   - What is the resulting new access level?

3. [ ] **Map to ATT&CK.** For each hop, record the technique ID and sub-technique ID. Look up the detection guidance on the ATT&CK page for each. Are any hops completely undetectable with the current Corp logging policy? Which ones?

4. [ ] **Identify the highest-value remediation.** Which single fix breaks the *most* paths to DA? Justify your answer. (Hint: consider what removing the GenericWrite ACE on IT-Admins would do to the path count, vs. what rotating svc-mssql's password would do.)

5. [ ] **Write the client narrative.** Draft a plain-English attack path section for a client report — three to five paragraphs that explain the path to a non-technical CISO. No tool names, no ATT&CK IDs — just "an attacker who gains access as a Finance employee can, in five steps, achieve complete control of the domain." Have a model draft it from your hop-by-hop notes, then fact-check every technical claim.

6. [ ] **Prioritised mitigation table.** Produce a table: hop number, technique, specific fix, effort (Low/Medium/High), and impact (how many paths does this break?). This is the client's remediation roadmap.

## Success criteria — you're done when

- [ ] You have a complete hop-by-hop analysis of the jsmith → DA path, with ATT&CK IDs and event IDs.
- [ ] You have identified the highest-priority single remediation with justification.
- [ ] You have a written client-facing narrative (3-5 paragraphs).
- [ ] You have a prioritised mitigation table.

## Deliverables

`attack-path-report.md` — the full report: hop analysis, ATT&CK mapping, client narrative, and prioritised mitigation table. This is a portfolio deliverable — the kind of document you'd include in a professional penetration test report. Commit it.

## Automate & own it

**Required.** Write `path-analyzer.py` — a Python script that reads `data/bloodhound-attack-paths.json` and outputs: the full path with technique IDs, a count of unique techniques used, and a "highest-leverage fix" recommendation based on which node/edge removal would break the most paths. Have a model draft the graph traversal logic; you verify it produces the correct hop count and that the "highest-leverage fix" logic is sound (not just picking the first hop). Commit it alongside the report.

## AI acceleration

Have a model generate the full client-report section from your hop-by-hop notes. Then do a structured review: for each paragraph, verify (1) the technique description is accurate, (2) the event ID mentioned is correct, (3) the mitigation is specific and actionable (not just "update password policies"). Mark any inaccuracy in red and fix it. The model is fast at prose; you are the accuracy check.

## Connects forward

The attack path and its detections feed directly into the Sigma rules in module 09. The mitigations become the hardening checklist items in module 10. The full path — attack and defence — is the basis for the module 11 capstone: a tiered admin model that breaks each hop structurally.

## Marketable proof

> "I trace multi-hop Active Directory attack paths in BloodHound, map each hop to ATT&CK, identify the highest-priority remediations, and produce a client-ready report that a CISO can use to drive a remediation roadmap."

## Stretch

- Write a Cypher query in BloodHound CE that finds *all* paths (not just shortest) from any Finance user to Domain Admins, and counts how many unique paths exist. Discuss what a "high path count" means for prioritisation.
- Research **graph-based prioritisation**: the concept of "choke points" in an attack graph — nodes whose removal breaks the most paths. Look at the BloodHound CE tier zero analysis as an implementation of this idea.

> **▶ Phase 2 project.** You've finished Phase 2 — now integrate these modules: [Phase 2 Project — Own the Domain](../../phase-2-project.md).
