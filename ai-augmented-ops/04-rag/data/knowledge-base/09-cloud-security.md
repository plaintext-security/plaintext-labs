# LastPass Breach — Cloud Storage and Key Custody
**Document type:** Practitioner analysis (grounded in the LastPass disclosures)

## The cloud backup environment was the prize
The data that ultimately leaked — customer account information and the encrypted vault backups —
lived in a **cloud-based storage service** used for **backups**, separate from production. The
attacker accessed it using **stolen credentials and the keys that decrypted the storage volumes**.

## Two distinct layers of "decryption keys"
A precise reading matters here:

1. **Storage-layer keys (compromised):** keys/credentials that unlock the cloud storage
   **volumes/containers**. The attacker obtained these (via the engineer's corporate vault) and used
   them to access and copy the backups.
2. **Per-customer vault keys (NOT compromised):** the AES-256 keys derived from each customer's
   **master password**, which protect the secrets inside each vault. LastPass does not hold these, so
   the attacker copied encrypted vault blobs they could not directly open.

Conflating these two is the most common error when summarizing this breach — the storage was
decrypted; the individual vault secrets were not.

## Cloud key-custody lessons
- **Where do storage decryption keys live, and who can reach them?** Here they were reachable from a
  small set of engineers' corporate vaults — and one of those was captured via a home-computer
  keylogger.
- **Backups in cloud storage are a top target.** They aggregate everything and may be monitored less
  than production. Apply production-grade access control, key custody, and alerting to backups.
- **Access via valid keys evades exploit-based detection.** Monitor for anomalous *use* of legitimate
  storage credentials (unusual principals, geographies, bulk reads), not just exploits.

## Source
- LastPass, "Notice of Recent Security Incident": https://blog.lastpass.com/posts/notice-of-recent-security-incident
