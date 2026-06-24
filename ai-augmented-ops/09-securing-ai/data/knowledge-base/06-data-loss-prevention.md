# LastPass Breach — Customer Guidance and Risk
**Document type:** Public post-mortem detail | **Source:** LastPass disclosure (Dec 22, 2022)

## What customers were told
LastPass's guidance depended on the strength of each customer's master password.

- **Default master-password configuration:** For customers whose accounts followed LastPass's
  default settings (a master password of at least 12 characters, with 100,100 rounds of PBKDF2 key
  derivation for accounts created since 2018), LastPass stated it would take an impractical amount of
  time to guess the master password with generally available password-cracking technology. These
  customers were told **no action was immediately required**.
- **Weaker or reused master passwords:** Customers with shorter master passwords, or who had reused
  their master password elsewhere, were advised to **change the passwords of websites stored in their
  vault** to minimize risk, because the stolen encrypted vaults could become crackable offline.

## Residual risk even with a strong master password
- The **website URLs** in the stolen backups were unencrypted, so attackers can see which services a
  customer uses and craft **targeted phishing** for those services.
- Customers were advised to be alert to phishing and social-engineering attempts referencing their
  LastPass account, and not to act on unsolicited messages asking for their master password (LastPass
  will never ask for it).

## Practitioner takeaways
- A breach of *encrypted* data is still a breach: cleartext metadata (URLs) and the threat of offline
  cracking against weak master passwords mean "it was encrypted" is not "no impact."
- Password reuse turns a single vault compromise into many account compromises — the case for unique
  passwords per site (the very thing a password manager exists to enable).

## Source
- LastPass, "Notice of Recent Security Incident": https://blog.lastpass.com/posts/notice-of-recent-security-incident
