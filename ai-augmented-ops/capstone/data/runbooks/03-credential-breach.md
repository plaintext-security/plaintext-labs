# Runbook — Credential / key compromise leading to cloud-backup exfiltration

**Class:** Valid Accounts (T1078) → Data from Cloud Storage (T1530). **Severity:** Critical.

## The reference case: LastPass, 2022
A two-stage breach worth indexing because the *pivot*, not the initial access, did the damage:
- **Stage 1 (Aug 2022):** a single compromised developer account gave an attacker access to the
  **development** environment — source code and technical info, but no customer data (dev was
  separated from production).
- **Stage 2 (Nov–Dec 2022):** the attacker used stage-1 information to target one of only **four
  DevOps engineers** with vault-decryption-key access, compromised that engineer's **personal home
  computer** via an unpatched **Plex Media Server** flaw (CVE-2020-5741), keylogged the master
  password after MFA, reached the corporate vault, and exfiltrated the **keys to AWS cloud backups**
  — then copied customer data and encrypted vault backups.
- Source: LastPass advisory <https://blog.lastpass.com/posts/notice-of-recent-security-incident>.

## Lessons that drive the response
- **Unmanaged privileged endpoints are critical attack surface.** A personal machine with vault
  access is in scope; treat it as such.
- **Separation worked for stage 1, not stage 2.** Network separation stopped the dev-account
  compromise reaching customers; it did nothing once decryption keys were stolen. Key custody, not
  just network boundaries, gates the crown jewels.
- **Cleartext-by-design fields still leak signal.** In the LastPass vault backup, website URLs were
  unencrypted even though passwords were AES-256 — the attacker learned *which* sites each customer
  used without cracking anything.

## Immediate actions
1. Revoke and rotate the suspected credentials/keys; force re-auth on dependent services.
2. Hunt for use of the stolen credential (impossible-travel logins, access from new ASNs, backup
   downloads).
3. Identify every secret the compromised principal could reach (the "blast radius of one key").
