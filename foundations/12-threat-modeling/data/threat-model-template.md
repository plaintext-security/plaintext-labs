# Threat Model — [System Name]

<!-- Template: fill in every section; delete placeholder text before submitting -->

**System:** [e.g. Meridian Financial Customer Portal]
**Modeler:** [Your name]
**Date:** [Date]

---

## 1. Data Flow Diagram (text form)

```
[Browser]
   |  HTTPS (TLS 1.3)
   ↓
[Web Server]           ← TRUST BOUNDARY: internet vs. DMZ
   |  SQL (parameterized)
   ↓
[Database]             ← TRUST BOUNDARY: DMZ vs. internal
```

Elements (list each):
- Browser (client — untrusted)
- Web Server (application tier)
- Database (data tier)

Flows (list each with protocol):
- Browser → Web Server: HTTPS/443
- Web Server → Database: SQL/5432

Trust boundaries (mark at least 2):
1. Internet / DMZ: between Browser and Web Server
2. DMZ / Internal: between Web Server and Database

---

## 2. STRIDE Threat Table

| # | Element / Flow         | Stride Letter | Threat (concrete)                                      | Mitigation                        | CIA Property |
|---|------------------------|---------------|--------------------------------------------------------|-----------------------------------|--------------|
| 1 | Browser → Web Server   | S (Spoofing)  | Attacker submits forged session cookie as another user | Signed, HttpOnly session token; rotate on login | Confidentiality |
| 2 | Web Server             | T (Tampering) | SQL injection modifies order records                   | Parameterized queries; WAF        | Integrity    |
| 3 | Web Server             | R (Repudiation) | User denies placing fraudulent order               | Tamper-evident audit log (append-only) | Integrity |
| 4 | Database               | I (Information disclosure) | DB credentials leaked via config file exposed | Secrets manager; no plaintext credentials in code | Confidentiality |
| 5 | Web Server             | D (Denial of service) | Login endpoint flooded, locks out all users    | Rate limiting; account lockout policy | Availability |
| 6 | Web Server → Database  | E (Elevation of privilege) | App DB user can DROP TABLE (over-privileged) | Least-privilege DB user; no DDL grants to app user | All three |

---

## 3. Top 2 controls to prioritise

1. **[Control]** — breaks threats # [list IDs] — protects [CIA] via [principle]
2. **[Control]** — breaks threats # [list IDs] — protects [CIA] via [principle]

---

## 4. AI reconciliation

Prompt used: "[paste prompt here]"

Model's STRIDE pass (summarise or paste key threats):
```
[model output here]
```

What I kept, changed, or added — and why:
- Kept: [...]
- Changed: [... because ...]
- Added: [... which the model missed ...]
