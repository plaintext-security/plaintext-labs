# Lab 03 — Kerberoasting & AS-REP Roasting

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/active-directory/03-kerberos-attacks
make up      # start Samba4 DC + impacket attacker container (~2 min first build)
make demo    # run Kerberoast + AS-REP roast, display hashes
make shell   # interactive impacket shell
make down    # stop when done
```

The `data/hashes.txt` file contains pre-generated Kerberoast ticket hashes for offline cracking practice — use these if you want to skip straight to hashcat.

> Authorization: this app is yours — attack it freely. The habit still matters everywhere else:
> only test systems you own or have explicit written permission to test (DVWA, PortSwigger Academy,
> targets you own).

## Scenario

As `jsmith` on the Meridian Financial network, you have enumerated the domain (module 02) and identified three Kerberoastable service accounts and two AS-REP roastable accounts. Your goal is to extract their ticket hashes and crack the weakest ones offline. A cracked service account password is the next step in the chain toward Domain Admin.

## Do

1. [ ] **Kerberoast all SPNs.** As `jsmith`, request a TGS for every account with an SPN and capture the ticket hashes to `spn-hashes.txt`. (Which Impacket tool requests SPNs and prints crackable hashes?) Note the hash format — what in the hash prefix tells you which encryption the KDC used for the ticket?

2. [ ] **Inspect the hash structure.** Open `spn-hashes.txt` and identify: which field carries the account name? Which is the encrypted ticket blob? Why does the etype drive cracking speed?

3. [ ] **AS-REP roast.** With no credential at all, request AS-REP material for accounts that don't require pre-authentication, feeding the tool a user list. Which accounts return a hash, and what prefix identifies an AS-REP hash? Why did this require no password?

4. [ ] **Crack the hashes offline.** Run hashcat against the sample hashes in `data/hashes.txt` with rockyou. (Which hashcat mode matches a TGS-REP etype-23 hash? Which matches an AS-REP hash?) Which account cracks, how long did it take, and what does that say about service-account password hygiene?

5. [ ] **Understand the etype downgrade.** Re-request the roast forcing AES256 instead of RC4 and compare the hash prefixes. Find the matching hashcat mode for the AES256 TGS and explain why AES makes cracking dramatically harder. Record both etype numbers and their hashcat modes in your notes.

6. [ ] **Map to ATT&CK.** Write down: which technique ID covers Kerberoasting? AS-REP roasting? For each, name the specific detection note from the ATT&CK page (Windows Event ID and the field to filter on).

## Success criteria — you're done when

- [ ] You have extracted Kerberoast hashes for all three SPNs and AS-REP hashes for both no-preauth accounts.
- [ ] At least one hash has been cracked with hashcat (or confirmed crackable using `data/hashes.txt`).
- [ ] You can explain why the attack leaves no lockout events.
- [ ] You have the ATT&CK technique IDs (T1558.003, T1558.004) and the specific Event ID that detects each.

## Deliverables

`kerberoast-report.md` — SPNs found, hashes extracted (truncated, not full — never commit full hashes), cracked accounts (by username and note about password weakness), ATT&CK mapping, and detection notes. Commit the report and your annotated `spn-hashes.txt` (with the hash blobs redacted to the first 20 chars).

## Automate & own it

**Required.** Write `kerberoast-scan.py` — a script that connects to the DC via impacket (use `GetUserSPNs`'s library functions, or shell out), extracts all SPNs, and outputs a summary: account name, SPN, password last set, etype. Have a model draft the impacket calls; you verify each API call against impacket's examples and confirm the output. This becomes a reusable domain health check. Commit it.

## AI acceleration

Ask a model: "Given a Kerberoast hash with etype 23 (RC4), estimate how many hashes per second hashcat achieves on a modern GPU and how long it would take to exhaust rockyou.txt." Then ask it the same for etype 18 (AES256). Use these estimates to explain to a client why migrating service accounts to gMSAs (which have 120-char random passwords) eliminates Kerberoasting entirely.

## Connects forward

The cracked `svc-mssql` or `svc-backup` credential is used for pass-the-hash in module 04. The `svc-backup` unconstrained delegation is abused in module 07 (persistence). Detection of Event 4769 with RC4 etype is the basis for the Sigma rule in module 09.

## Marketable proof

> "I execute Kerberoasting and AS-REP roasting against Active Directory, recover offline-crackable ticket hashes, and explain both the attack mechanics and the specific audit configuration required to detect it."

## Stretch

- Try requesting a TGS for a service account that *does* require AES — is there a way to force RC4 that the KDC allows? Research the `msds-SupportedEncryptionTypes` attribute and what setting forces AES-only.
- Write a Cypher query in BloodHound CE that marks all Kerberoastable accounts (has SPN + not in Protected Users + password age > 1 year) — this is what a real attack-path analysis surfaces automatically.
