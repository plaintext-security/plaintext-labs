# Alert Triage Accuracy Report
## Log4Shell exploitation wave (CVE-2021-44228) — AI Triage Validation

**Date:** <!-- fill in -->
**Model:** <!-- e.g. tinyllama -->
**Total alerts evaluated:** 50

---

## Overall accuracy

**Accuracy:** <!-- e.g. 72% -->

---

## Confusion matrix

| True \ Predicted | CRITICAL | HIGH | MEDIUM | LOW |
|-----------------|----------|------|--------|-----|
| CRITICAL | | | | |
| HIGH | | | | |
| MEDIUM | | | | |
| LOW | | | | |

---

## Per-class metrics

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| CRITICAL | | | |
| HIGH | | | |
| MEDIUM | | | |
| LOW | | | |

---

## False negatives on CRITICAL/HIGH alerts

<!-- List any CRITICAL or HIGH alerts the model classified below their true severity -->

| Alert ID | True severity | Predicted | Notes |
|----------|--------------|-----------|-------|
| | | | |

---

## False negative analysis

**Alert ID:** <!-- which alert was the most concerning false negative? -->
**True severity:** <!-- e.g. CRITICAL -->
**Predicted severity:** <!-- e.g. MEDIUM -->

**Root cause:**
<!-- Was it a retrieval miss? Ambiguous alert text? Hallucination? Prompt bias issue?
     Explain in 2–3 sentences. -->

**Prompt improvement made:**
<!-- Describe the change to the prompt in triage.py -->

**Re-test result:**
<!-- Did the change fix the false negative? Did it introduce new false positives? -->

---

## Recommendation

<!-- One paragraph: is the pipeline accurate enough to use for this alert queue?
     What accuracy threshold would you require before deploying to production?
     Cite the recall rate on CRITICAL alerts as the key metric. -->
