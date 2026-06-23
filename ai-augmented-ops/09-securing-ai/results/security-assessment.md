# AI Copilot Security Assessment
## SOC Copilot — Red Team Findings

**Date:** <!-- fill in -->
**Tester:** <!-- fill in -->
**Scope:** Module 06 SoC Copilot (Ollama + ChromaDB + copilot app)

---

## Attack 1 — Prompt Injection via Alert Text

**OWASP:** LLM01  **MITRE ATLAS:** AML.T0051

**Observed behaviour (pre-mitigation):**
<!-- What did the copilot output when given the injected alert? Did it follow the
     injected instruction? What was the severity it reported? -->

**Mitigation implemented:**
<!-- Describe the sanitise_input() function you added to copilot.py. What patterns
     does it strip? How does it handle edge cases? -->

**Post-mitigation behaviour:**
<!-- Re-run make attack-injection after the fix. Does the injection still affect output?
     What changed? -->

**Residual risk:**
<!-- What injection techniques still work? What would defeat the filter? -->

---

## Attack 2 — Corpus Poisoning

**OWASP:** LLM09  **MITRE ATLAS:** AML.T0016

**Observed behaviour (pre-mitigation):**
<!-- Did the poisoned runbook surface in the retrieval results? Did the model quote
     the attacker's contact email in its ransomware response recommendation? -->

**Mitigation implemented:**
<!-- Describe the output validation check you added. What allowlist does it use?
     How does it handle a flagged answer? -->

**Post-mitigation behaviour:**
<!-- Does the output validation catch the malicious URL in the generated answer? -->

**Residual risk:**
<!-- What corpus poisoning techniques bypass the URL filter? Can the attacker avoid
     using a URL and still inject malicious guidance? -->

---

## Attack 3 — MCP Tool Abuse (Input Validation)

**OWASP:** LLM07

**Observed behaviour:**
<!-- What did the search_alerts tool return for a 2000-char query? Error dict or crash? -->

**Mitigation status:**
<!-- Was the validation already in place from Module 05? Did it hold? -->

**Residual risk:**
<!-- Are there any tool inputs that the current validation misses? -->

---

## Overall risk rating

| Attack | Pre-mitigation | Post-mitigation | Residual risk |
|--------|---------------|----------------|---------------|
| Prompt injection (alert text) | CRITICAL | | |
| Corpus poisoning | HIGH | | |
| Tool input abuse | MEDIUM | | (mitigated in Module 05) |

---

## Recommendations

<!-- Three one-sentence recommendations for the security team before the
     copilot goes to production. Cite OWASP LLM risks by ID, and tie each to its real-world
     precedent in data/real-incidents.json (EchoLeak / Chevy / Air Canada / Invariant MCP). -->
