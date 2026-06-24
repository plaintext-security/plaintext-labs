# Threat Model — SOC Copilot
## AI Security Assessment

**Date:** <!-- fill in -->
**System:** SOC Copilot — Ollama (tinyllama) + ChromaDB RAG + MCP tools

## Real-world precedents (the documented incidents this model defends against)

Each attack class below is grounded in a *real, public* incident — not an invented scenario:

| Attack class | Documented precedent | Reference |
|--------------|----------------------|-----------|
| Direct prompt injection / jailbreak (a system prompt is not a control) | Chevrolet of Watsonville "$1 Tahoe" jailbreak (2023) | [vectara case study](https://github.com/vectara/awesome-agent-failures/blob/main/docs/case-studies/chevrolet-dealership-chatbot.md) |
| Indirect (zero-click) injection + data exfil via retrieved context | EchoLeak — CVE-2025-32711 in M365 Copilot (2025) | [NVD CVE-2025-32711](https://nvd.nist.gov/vuln/detail/CVE-2025-32711) |
| Malicious tool descriptions / tool-call abuse | Invariant Labs MCP Tool Poisoning (2025) | [Invariant Labs](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks) |
| Downstream liability of unguarded AI output | Moffatt v. Air Canada (2024 BCCRT 149) | 2024 BCCRT 149 |

OWASP LLM Top 10 (2025), LLM01 Prompt Injection: https://genai.owasp.org/llmrisk/llm01-prompt-injection/

---

## Adversaries

| Adversary | Motivation | Access level | Likely technique |
|-----------|-----------|--------------|-----------------|
| External attacker (alert injection) | Reclassify high-severity alerts as low to avoid detection | Indirect — via malicious endpoint sending alerts | Prompt injection via alert text (ATLAS AML.T0051) |
| Insider threat (corpus poisoning) | Manipulate analyst response recommendations | Direct — write access to knowledge base ingestion | Corpus poisoning (ATLAS AML.T0016) |
| Sophisticated attacker (combined) | Persistent access to the SOC environment | Indirect, persistent | Combined corpus poisoning + prompt injection (the EchoLeak shape) |

---

## Assets

| Asset | Value to attacker |
|-------|-----------------|
| Alert severity classifications | Reclassify CRITICAL to LOW → avoid containment |
| System prompt content | Understand instructions → craft targeted injections |
| Knowledge base contents | Exfiltrate internal runbooks and incident data |
| MCP tool capabilities | Abuse tool calls for lateral movement or recon |

---

## Attack surface

| Surface | Threat | Untrusted input? |
|---------|--------|----------------|
| Alert text (description, title) | Prompt injection | Yes — comes from endpoints/EDR |
| Tool results (threat intel, alerts) | Tool output poisoning | Yes — data from external or manipulated stores |
| RAG retrieved chunks | Corpus poisoning | Yes — if ingestion pipeline is not access-controlled |
| Model API | Direct probing, jailbreak | Yes — if API is exposed beyond localhost |
| MCP tool arguments | Tool abuse via oversized/malicious input | Yes — model-generated |

---

## Top 3 threats

### Threat 1 — Severity Manipulation via Alert Injection
**OWASP:** LLM01 — Prompt Injection
**MITRE ATLAS:** AML.T0051 — LLM Prompt Injection
**Named precedent:** EchoLeak / CVE-2025-32711 — injection that rides in on data the model retrieves (here, alert text); and the Chevy "$1 Tahoe" jailbreak — a system prompt is not the control.
**Likelihood:** HIGH — alert data is inherently untrusted
**Impact:** CRITICAL — missed alert → undetected breach
**Mitigations implemented:** Input sanitisation (Module 09), severity output validation
**Residual risk:** <!-- describe what still works after mitigation -->

### Threat 2 — Runbook Corruption via Corpus Poisoning
**OWASP:** LLM09 — Overreliance
**MITRE ATLAS:** AML.T0016 — Obtain Capabilities
**Named precedent:** EchoLeak / CVE-2025-32711 (the poisoned-document delivery vector); and Moffatt v. Air Canada (2024 BCCRT 149) — the org owns the consequence when an analyst acts on the poisoned answer.
**Likelihood:** MEDIUM — requires write access to ingestion pipeline
**Impact:** HIGH — analyst follows poisoned guidance during incident
**Mitigations implemented:** Output URL validation (Module 09), corpus access control
**Residual risk:** <!-- describe what still works after mitigation -->

### Threat 3 — System Prompt Extraction / Tool-Surface Abuse via Leakage
**OWASP:** LLM02 — Insecure Output Handling
**MITRE ATLAS:** AML.T0054 — LLM Jailbreak
**Named precedent:** Invariant Labs MCP Tool Poisoning (2025) — tool descriptions and tool arguments are an attack surface; leaking the prompt/tooling enables targeted follow-on injection.
**Likelihood:** MEDIUM — requires attacker to interact with the copilot API
**Impact:** MEDIUM — knowledge of system prompt enables more targeted injections
**Mitigations implemented:** Model-level resistance (tested by garak/promptfoo)
**Residual risk:** <!-- describe what still works after mitigation -->

---

## Mitigations implemented

| Mitigation | Module | Coverage |
|-----------|--------|---------|
| Input sanitisation (strip injection patterns) | 09 | Prompt injection via alert text |
| Output URL validation | 09 | Corpus poisoning via malicious runbook |
| MCP tool input validation | 05 | Tool abuse via oversized input |
| Corpus ingestion access control | 09 | Corpus poisoning |

---

## Residual risk summary

<!-- One paragraph: after all implemented mitigations, what threats remain open?
     What would be required to close them? What is the acceptable risk threshold
     for production deployment of this copilot? -->
