# LastPass Breach — Stage 2: Cloud Backup Storage Exfiltration (Nov–Dec 2022)
**Document type:** Public post-mortem detail | **Source:** LastPass disclosures (Nov 30 & Dec 22, 2022)

## Summary
In the second incident, the threat actor **leveraged information obtained from the August 2022
incident** to target a second LastPass employee, obtained credentials and keys, and used them to
**access and decrypt storage volumes** within a cloud-based **backup** environment. From there the
attacker copied customer account information and customer vault backups.

## How the attacker reached the cloud backup storage
1. The attacker reused information stolen in stage 1 (source code and technical documentation).
2. They targeted a **second employee** to obtain that employee's credentials and keys.
3. Those credentials and keys were used to access the third-party cloud storage service holding
   LastPass backups — an environment **separate from production**.
4. The attacker obtained the **decryption keys needed to open the storage volumes** (dual storage
   container decryption keys), allowing them to decrypt and copy the backup contents.

## What was exfiltrated
- **Basic customer account information and metadata:** company names, end-user names, billing
  addresses, email addresses, telephone numbers, and the IP addresses from which customers accessed
  the LastPass service.
- **A backup of customer vault data**, containing both unencrypted and encrypted fields (see document
  04 for the encryption detail).
- LastPass found **no evidence** that unencrypted credit card data was accessed.

## Why "decrypt" appears in a backup breach
A common confusion: the *vault contents* (passwords) remained AES-256 encrypted under each
customer's master password. The keys the attacker stole were the **storage-layer** keys that
decrypted the storage *volumes/containers* — not the per-user vault encryption. The attacker got the
encrypted vault blobs out of storage, but still faced the customer master-password encryption on the
secrets inside them.

## Key facts
- Initial pivot: information from **stage 1** reused to target a **second employee**.
- Target: cloud-based **backup** storage (not production).
- Attacker obtained **credentials + storage decryption keys**.
- Exfiltrated: customer account data **and** encrypted vault backups.

## Source
- LastPass, "Notice of Recent Security Incident": https://blog.lastpass.com/posts/notice-of-recent-security-incident
