# SoC Copilot Evaluation
## Copilot Validation — manual reasoning-chain log

This is the human-readable companion to the automated scorecard (`copilot-scorecard.md`). Use it to
record what you observed in the reasoning chain for a handful of questions before trusting the
numbers. The institutional-knowledge corpus is the **LastPass 2022 breach** post-mortem (reused from
Module 04); the live alert/incident/threat-intel seed data is a **Log4Shell (CVE-2021-44228)**
incident.

**Date:** <!-- fill in -->
**Tester:** <!-- fill in -->
**Model:** <!-- e.g. tinyllama -->

---

## Question 1: Is 192.0.2.66 malicious? (make demo)

**RAG chunks retrieved (sources):** <!-- list filenames -->
**Tools called:** <!-- e.g. get_threat_intel(192.0.2.66) -->
**Tool result summary:** <!-- e.g. found: true, classification: malicious, category: Log4Shell exploit/LDAP callback + payload host -->
**Generated answer:**
```
<!-- paste answer -->
```

| Criterion | Result | Notes |
|-----------|--------|-------|
| Retrieved chunks relevant | | |
| Tool call correct | | |
| Answer cites sources | | |
| Hallucination observed | | |

---

## Question 2: Ransomware / stage-2 containment reasoning

**RAG chunks retrieved:** <!-- -->
**Tools called:** <!-- -->
**Generated answer:**
```
```

| Criterion | Result | Notes |
|-----------|--------|-------|
| Retrieved chunks relevant | | |
| Answer cites sources | | |
| Hallucination observed | | |

---

## Question 3: Open incident for host SRV-WEB01

**RAG chunks retrieved:** <!-- -->
**Tools called:** <!-- expect search_alerts(SRV-WEB01) -->
**Generated answer:**
```
```

**Diagnosis (if wrong):** <!-- retrieval miss / tool error / hallucination-on-context -->

---

## Question 4: LastPass — was the copied vault data encrypted?

**RAG chunks retrieved:** <!-- expect 04-detection-notes-lateral-movement.md -->
**Tools called:** <!-- expect none -->
**Generated answer:**
```
```

---

## Question 5: LastPass stage-2 home-computer vector summary

**RAG chunks retrieved:** <!-- expect 05-phishing-runbook.md -->
**Tools called:** <!-- expect none -->
**Generated answer:**
```
```

**Must-have facts (rubric):** Plex Media Server / CVE-2020-5741 · keylogger · one of four DevOps
engineers · master password captured after MFA · reached AWS cloud backup keys.

---

## Failure mode diagnosed

**Question:** <!-- which question failed? -->
**Failure type:** Retrieval miss / Tool call error / Hallucination-on-context
**Root cause:** <!-- explain -->
**Improvement implemented:** <!-- describe the change to copilot.py -->
**Re-test result:** <!-- did the improvement fix it? -->
