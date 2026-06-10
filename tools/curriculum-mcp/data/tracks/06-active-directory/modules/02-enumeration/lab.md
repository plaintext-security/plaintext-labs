# Lab 02 — Enumerate the Meridian Domain

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

This is a **reference lab** — the environment lives in the companion repo:

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/active-directory/02-enumeration
make up      # start Samba4 DC + attacker container (~2 min first build)
make demo    # run automated ldapsearch enumeration queries
make shell   # drop into the attacker container to run your own queries
make down    # stop everything when done
```

The lab provides:
- `samba-dc` — a Samba4 container acting as `dc01.meridian.local` with 30+ pre-seeded users and all the misconfigurations from `data/meridian-domain.md`.
- `attacker` — a Debian container with `ldapsearch`, `enum4linux-ng`, and `bloodhound-python` installed, pre-configured to reach the DC.
- `data/bloodhound-meridian.json` — a pre-generated BloodHound dataset for the Meridian domain (import this into BloodHound CE if you want the graph without running the full ingestor).

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Scenario

You're a red teamer who has just obtained credentials for `jsmith` (password: `Welcome1!`) on the Meridian Financial network. Your goal is to enumerate the entire domain — users, groups, service accounts, SPNs, and delegation settings — and build a BloodHound graph that shows the attack paths available from `jsmith`.

## Do

1. [ ] **Baseline with enum4linux-ng.** Point an all-in-one enumerator at the DC with your `jsmith` credential and record what it surfaces with no LDAP filters written. How many users, groups, and shares? What would a null session (no credential) have returned instead, and why is that a finding in itself?

2. [ ] **Raw LDAP — user enumeration.** Bind to the DC over LDAP as `jsmith` and pull every user object, requesting `sAMAccountName`, `userPrincipalName`, and `memberOf`. Save the output, count the accounts, and flag the ones that are clearly not human users.

3. [ ] **Find Kerberoastable accounts.** Narrow your filter to only user objects that carry a `servicePrincipalName`. List the SPNs and cross-reference `data/meridian-domain.md` — did you find all three Kerberoastable accounts? (Hint: this is a bitwise-AND of two object conditions.)

4. [ ] **Find AS-REP roastable accounts.** Filter on the `DONT_REQUIRE_PREAUTH` bit of `userAccountControl`. Which accounts have it set, and why is each exploitable with no password at all? (Hint: you'll need the LDAP bitwise-AND matching rule OID and the flag's decimal value — look them up.)

5. [ ] **Find unconstrained delegation.** Filter on the `userAccountControl` bit for unconstrained delegation. Which accounts appear, and why does the list always include DCs?

6. [ ] **Run bloodhound-python.** Collect a full BloodHound dataset from the DC as `jsmith`, producing a ZIP. Import it into BloodHound CE, or examine the raw JSON inside the ZIP. (If you'd rather skip the ingest, `data/bloodhound-meridian.json` is a pre-generated dataset for the same domain.)

7. [ ] **Analyse the BloodHound data.** From the graph or the raw JSON, answer: what is the shortest path from `jsmith` to `Domain Admins`? How many hops, and what is the edge type of each (e.g., `MemberOf`, `GenericWrite`, `CanPSRemote`)?

## Success criteria — you're done when

- [ ] You have a complete list of Meridian users, groups, and computers from ldapsearch.
- [ ] You have identified all three Kerberoastable SPNs and both AS-REP roastable accounts.
- [ ] You have identified the unconstrained delegation accounts.
- [ ] You have a BloodHound dataset (generated or from `data/`) imported and can answer "shortest path from jsmith to DA" with specific hops and edge types.
- [ ] You have written down what a defender would see in DC event logs for each query you ran.

## Deliverables

`enumeration-report.md` — a structured list of findings: users/groups/SPNs/delegation flags discovered, the shortest path to DA with edge types, and your notes on detection opportunities. Commit it.

## Automate & own it

**Required.** Write `enumerate.py` — a Python script using `ldap3` (or subprocess + ldapsearch) that queries the DC, collects all users with SPNs, all users without pre-auth, and all accounts with unconstrained delegation, and prints a clean summary. Have a model draft it; you verify the LDAP filter strings match what you ran manually and confirm the output against your ldapsearch results. Commit the script next to your report.

## AI acceleration

Paste the raw BloodHound JSON for a node into a model and ask it to explain the attack paths in plain English. It's good at translating graph data into narrative — but you must verify each edge type exists in BloodHound's schema (e.g., `GenericWrite` is real; some model-invented edges are not). The BloodHound GitHub has the canonical edge type list.

## Connects forward

The Kerberoastable SPNs you found here are the targets in module 03. The ACL edges in BloodHound (`GenericWrite`, `WriteDacl`) are the abuse paths in module 05. The full BloodHound dataset is the basis for the path analysis in module 08.

## Marketable proof

> "I enumerate Active Directory environments from a standard domain credential — LDAP, RPC, BloodHound — and produce a structured attack-surface map including privilege paths, Kerberoasting targets, and delegation risks."

## Stretch

- Write a Cypher query (paste into BloodHound CE's raw query interface) that finds all users with `GenericWrite` on a group, and all groups that have `AdminTo` rights on at least one computer. Interpret what each result means for an attacker.
- Research `ldap-monitor` or `ldapdomaindump` as alternative enumeration tools and note what each surfaces differently from ldapsearch.
