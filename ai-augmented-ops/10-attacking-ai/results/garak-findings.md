# garak Vulnerability Scan Results
## SOC Copilot — Model Assessment

**Date:** <!-- fill in -->
**Model:** tinyllama (via ollama:0.3.14)
**garak version:** <!-- fill in -->
**Scan type:** Fast (injection + leakage probes)

---

## Probe summary

| Probe class | Pass rate | Finding? | Description |
|-------------|-----------|----------|-------------|
| injection.* | <!-- % --> | Y/N | Prompt injection resistance |
| leakage.* | <!-- % --> | Y/N | System prompt extraction resistance |
| <!-- add others from full scan --> | | | |

**Threshold:** Probes with pass rate < 80% are classified as findings.

---

## Finding 1 — [Probe class name]

**Pass rate:** <!-- % -->
**Attack technique:** <!-- what does this probe class test? -->

**SOC context impact:**
<!-- In the context of a SOC assistant: what could an attacker do if this technique succeeds?
     Be specific: "an adversary could override the severity classification of a ransomware
     alert" is more useful than "an adversary could manipulate the model." -->

**Applicable OWASP LLM risk:** LLM<!-- number --> — <!-- name -->
**Applicable MITRE ATLAS technique:** AML.T<!-- number --> — <!-- name -->
**Named incident it rhymes with:** <!-- Chevy "$1 Tahoe" jailbreak / EchoLeak CVE-2025-32711 / Invariant MCP tool poisoning / Air Canada 2024 BCCRT 149 — see results/threat-model.md -->

**Mitigation:**
<!-- Which mitigation from Module 09 addresses this? If none, what new control would you add? -->

---

## Finding 2 — [Probe class name]

**Pass rate:** <!-- -->
**Attack technique:** <!-- -->
**SOC context impact:** <!-- -->
**Applicable OWASP LLM risk:** <!-- -->
**Mitigation:** <!-- -->

---

## Summary

**Total findings (pass rate < 80%):** <!-- -->
**Most critical finding:** <!-- -->
**Recommendation before production deployment:** <!-- one sentence -->
