# RAG Pipeline Evaluation
## Knowledge Base: LastPass 2022 Breach — Public Post-Mortem Corpus

The corpus is built from LastPass's public disclosures of the 2022 breach.
Primary source: https://blog.lastpass.com/posts/notice-of-recent-security-incident

**Date:** <!-- fill in -->
**Tester:** <!-- fill in -->
**Model (generation):** <!-- e.g. tinyllama -->
**Model (embedding):** nomic-embed-text

---

## Demo query (make demo)

**Question:** How did the attacker access the cloud backup storage in the LastPass breach?

**Ground truth (from the corpus):** The attacker reused information stolen in the first
(development-environment) incident to target a second employee — a DevOps engineer — compromised that
engineer's home computer via a vulnerable third-party media-server package, implanted a keylogger,
captured the master password to the engineer's corporate vault, and used the credentials/keys inside
to access and decrypt the cloud backup storage volumes. (Documents 03 and 05.)

**Retrieved chunks (sources):**
- <!-- list the source filenames returned -->

**Generated answer:**
```
<!-- paste the answer here -->
```

**Evaluation:**
| Criterion | Pass / Fail / Partial | Notes |
|-----------|----------------------|-------|
| Chunks relevant to the question | | |
| Answer supported by retrieved chunks | | |
| Hallucination-on-context observed | | |

---

## Query 2 — Initial access vector

**Question:** What was the initial access vector of the first LastPass incident?

**Ground truth:** A single compromised **developer account** gave access to the **development**
environment (separated from production); source code and technical information were taken; no customer
data or vaults were accessed. (Document 02.)

**Retrieved chunks (sources):** <!-- -->

**Generated answer:**
```
```

**Evaluation:**
| Criterion | Pass / Fail / Partial | Notes |
|-----------|----------------------|-------|
| Chunks relevant | | |
| Answer grounded in chunks | | |
| Hallucination observed | | |

---

## Query 3 — Encryption of vault data

**Question:** Was customer vault data encrypted in the stolen backups?

**Ground truth:** Mixed. Website **URLs were unencrypted**; usernames, passwords, secure notes, and
form-fill data were **AES-256 encrypted** under each customer's master password. (Document 04.)

**Evaluation:** <!-- -->

---

## Query 4 — Home-computer vulnerability

**Question:** What software was exploited on the engineer's home computer?

**Ground truth:** A vulnerable **third-party media-server software package** on the DevOps engineer's
home computer, enabling RCE and a keylogger. (Document 05.)

**Retrieved chunks (sources):** <!-- -->

**Generated answer:**
```
```

**Evaluation:** <!-- -->

---

## Out-of-corpus query — Unrelated policy

**Question:** What is LastPass's policy on cryptocurrency payments?

**Retrieved chunks (sources):** <!-- Were irrelevant chunks returned, or none? -->

**Generated answer:**
```
```

**Behaviour observed:** <!-- Did the model say "I don't have enough information"? Did it hallucinate a policy? -->

---

## New document retrieval

**Document added:** <!-- filename -->
**Query used:** <!-- what did you ask? -->
**Retrieved:** Yes / No
**Notes:** <!-- -->
