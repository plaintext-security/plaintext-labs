# Module 03 — Kerberos Attacks

*Type 5 · Detonate & Detect — execute Kerberoasting (T1558.003) and AS-REP roasting (T1558.004) against a live Samba4 AD domain, crack at least one recovered ticket hash offline, and pin the detection seam (the RC4-downgrade in Event 4769) that explains why the attack is otherwise invisible. (Secondary: Blast-Radius Trace — show which service accounts the roast opens onward.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Active Directory & Windows Security** — *Kerberos was designed for a world where everyone on the network is trusted; Active Directory inherited that assumption and never fully escaped it.*

<!-- module-meta -->
**Difficulty:** Advanced &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters

Kerberoasting and AS-REP roasting are in the top MITRE ATT&CK technique lists for a reason: they are fully authenticated, use the normal Kerberos protocol, generate no logon failures, and produce offline-crackable hashes. A domain with even one service account on a weak password is vulnerable. The detection requires specific audit settings that most environments don't have, and even with them, the signal is easy to miss. Understanding these attacks at the protocol level — not just running a tool — is what allows you to tune both the attack and the defence. And when the protocol itself is broken, a single Kerberos flaw becomes instant domain takeover: the **noPac** chain — [CVE-2021-42278](https://nvd.nist.gov/vuln/detail/CVE-2021-42278) (sAMAccountName spoofing) paired with [CVE-2021-42287](https://nvd.nist.gov/vuln/detail/CVE-2021-42287) (PAC confusion in the KDC), both CISA KEV-listed — let any authenticated user rename a controlled machine account to impersonate a domain controller and obtain a TGT as a DC.

## Objective

Execute Kerberoasting (T1558.003) and AS-REP roasting (T1558.004) against a live Samba4 AD domain, recover ticket hashes, and crack at least one password offline. Explain why the attack is undetectable without specific audit configuration.

## The core idea

The Kerberos protocol was designed with a subtle trust model: when a client wants to talk to a service, it asks the KDC for a **service ticket (TGS)**, which the KDC encrypts with the **service account's password hash**. The client receives this encrypted blob and delivers it directly to the service — no one checks that the client actually *uses* the ticket to do anything legitimate. **Kerberoasting** exploits this: any authenticated domain user can request a service ticket for any SPN in the domain, receive the KDC's encrypted blob, and then take it offline to crack. The attack is entirely protocol-compliant. There is no brute-force lockout, no failed logon, no authentication anomaly. The only observable signal is the TGS-REQ on the wire or a Windows Event 4769 on the DC — and only if you're logging and watching for Kerberoasting-shaped patterns (RC4 encryption type from an account that normally uses AES).

**AS-REP roasting** targets a different design choice: Kerberos pre-authentication. In normal Kerberos, the client proves it knows the password before the KDC issues a TGT — it encrypts a timestamp with the user's key, and the KDC checks it. This prevents an offline attack on the TGT. But if an account has the `DONT_REQUIRE_PREAUTH` flag set — a configuration option that exists for legacy application compatibility — any unauthenticated attacker can send an AS-REQ for that account and the KDC will respond with an AS-REP, part of which is encrypted with the user's password hash. Again: offline crackable, no failed logon, and the account doesn't have to have an SPN. It's the same fundamental issue — the KDC handing out encrypted material derived from the user's password.

The practical hierarchy of risk: **AS-REP roasting is more dangerous** (requires no credentials at all) but less common because the `DONT_REQUIRE_PREAUTH` flag is obvious and easy to audit. **Kerberoasting is more common** because SPNs are legitimate and abundant in any real environment, and service account passwords are often stale because nobody wants to update them across all the applications that use them. The realistic attack chain is: Kerberoast a service account with a weak/old password, crack it offline with hashcat, then use that credential to move laterally or escalate.

The encryption type matters: a TGS encrypted with **RC4** (etype 23) cracks orders of magnitude faster than one encrypted with **AES256** (etype 18). Some tools request RC4 explicitly even when the service account supports AES — the KDC allows the downgrade by default, and the downgrade from AES to RC4 is the most reliable detection signal. Defenders: configure audit policy for Event 4769 and alert on RC4 service tickets for accounts that normally use AES.

## Learn (~3 hrs)

**Kerberos background**
- [Kerberoasting without Mimikatz (Sean Metcalf / adsecurity.org)](https://adsecurity.org/?p=2293) — the original research paper that named and explained Kerberoasting. Read the explanation of why the protocol allows this, not just the tool commands.
- [T1558.003 — Kerberoasting (MITRE ATT&CK)](https://attack.mitre.org/techniques/T1558/003/) — the formal description with procedure examples and detection guidance. Read the detection section carefully.

**AS-REP roasting**
- [T1558.004 — AS-REP Roasting (MITRE ATT&CK)](https://attack.mitre.org/techniques/T1558/004/) — detection guidance and mitigations. Note that the mitigation is simply: audit for the flag and remove it.

**noPac — sAMAccountName spoofing to DC compromise**
- [CVE-2021-42278 (NVD)](https://nvd.nist.gov/vuln/detail/CVE-2021-42278) and [CVE-2021-42287 (NVD)](https://nvd.nist.gov/vuln/detail/CVE-2021-42287) — the two AD Domain Services elevation-of-privilege CVEs that combine into noPac. Read both summaries: 42278 is the sAMAccountName spoof, 42287 is the KDC's PAC mix-up that turns the spoof into a DC-level TGT. Both are KEV-listed; the fix is the November 2021 patch.

**Impacket toolkit**
- [Impacket (GitHub — SecureAuthCorp/impacket)](https://github.com/fortra/impacket) — the Python library and toolkit used for the attacks. Read the `examples/` README for `GetUserSPNs.py` and `GetNPUsers.py`.

**Offline cracking**
- [Hashcat wiki — Kerberos hashes](https://hashcat.net/wiki/doku.php?id=hashcat) — understand the hash modes: `-m 13100` for Kerberoast RC4 TGS, `-m 19600` for AES256 TGS, `-m 18200` for AS-REP. The performance difference between modes is the reason attackers prefer RC4.

## Key concepts
- Any authenticated user can request a TGS for any SPN — this is by design.
- Kerberoasting = request TGS, receive RC4-encrypted blob, crack offline. No lockout.
- AS-REP roasting = request AS-REP for an account with `DONT_REQUIRE_PREAUTH`, crack offline. No credentials needed.
- RC4 (etype 23) cracks ~10× faster than AES256 (etype 18) — the encryption type downgrade is the detection signal.
- Windows Event 4769 with RC4 encryption type from a non-RODC service account is the primary detection indicator.
- noPac (CVE-2021-42278 + CVE-2021-42287) chains sAMAccountName spoofing with a KDC PAC flaw so any authenticated user impersonates a DC — patch (Nov 2021) and alert on machine-account renames.
- Mitigation: strong, unique, regularly rotated service account passwords; prefer Managed Service Accounts (MSAs/gMSAs) which have 120-char random passwords.

## AI acceleration

Use a model to explain the PAC (Privilege Attribute Certificate) structure inside a Kerberos ticket — it's not well documented in a single place. Ask it to walk through what fields `GetUserSPNs.py` parses to produce the hashcat-formatted output. Then verify against the impacket source (`impacket/krb5/ccache.py`, `impacket/krb5/kerberosv5.py`) — the model's explanation should match the code.
