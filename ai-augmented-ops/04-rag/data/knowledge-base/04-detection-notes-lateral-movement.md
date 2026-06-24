# LastPass Breach — What Was Encrypted vs. In Cleartext
**Document type:** Public post-mortem detail | **Source:** LastPass disclosure (Dec 22, 2022)

## The copied vault backup contained two kinds of data
The customer vault backup the attacker copied was **not uniformly encrypted**. It was a mix:

- **Unencrypted fields:** website **URLs**. Because URLs were stored in the clear, the attacker can
  see *which sites* a given customer had credentials for, even without cracking anything.
- **Encrypted fields:** website **usernames and passwords, secure notes, and form-filled data**.
  These were protected with **256-bit AES** encryption and can only be decrypted with the customer's
  unique **master password**, which LastPass states it does not know or store.

## What this means in practice
- The secrets themselves (passwords, notes) stay protected **as long as the master password is
  strong** and was not phished or reused elsewhere.
- The cleartext URLs are still sensitive: they reveal a customer's account footprint and enable
  targeted phishing against the specific services that customer uses.
- Credit card data: LastPass found **no evidence** that unencrypted credit card data was accessed.

## Master-password strength is the whole defense
LastPass's encryption uses PBKDF2 key derivation (100,100 iterations for accounts created under the
2018+ default). LastPass stated that with a strong default master password (12+ characters) it would
take an impractical amount of time to brute-force the encryption. The corollary — and the real
risk — is **weak or reused master passwords**, where offline cracking of the stolen encrypted vaults
becomes feasible.

## Key facts
- **Cleartext in the backup:** website URLs.
- **Encrypted in the backup (AES-256, master-password-derived key):** usernames, passwords, secure
  notes, form-fill data.
- Defense rests on **master-password strength**; LastPass cannot decrypt vaults for the customer.

## Source
- LastPass, "Notice of Recent Security Incident": https://blog.lastpass.com/posts/notice-of-recent-security-incident
