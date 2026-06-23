# AI Task Routing Decision Matrix
## Security Operations AI Pilot

Use this matrix to decide whether a security task should run on a **Local** model (Ollama,
on-premises), a **Frontier** model (hosted API, cloud provider), or be **Human-only** (AI
may assist preparation, but a human makes the final call or holds the data).

> **Grounded in real incidents.** The routing intuition below is built from two named cases,
> not invented scenarios:
> - **Moffatt v. Air Canada (2024 BCCRT 149)** — an airline's website chatbot confidently told a
>   customer he could claim a bereavement fare retroactively; the airline's real policy did not
>   allow it. The tribunal found negligent misrepresentation and held the airline liable for what
>   its AI said (award C$812.02). Lesson: an org owns its AI's customer-facing output, so
>   high-stakes / irreversible tasks route to **Human-only** or require human-verifiable grounding.
>   <https://www.canlii.org/en/bc/bccrt/doc/2024/2024bccrt149/2024bccrt149.html>
> - **EchoLeak — CVE-2025-32711** — a zero-click indirect prompt-injection in Microsoft 365 Copilot
>   (Aim Security; CVSS 9.3; patched May 2025) that exfiltrated sensitive internal data a model had
>   pulled into context via RAG. This is exactly the **LLM06 — Sensitive Information Disclosure**
>   exposure, and it is why unredacted internal data favours a **Local / on-prem** model rather than
>   a cloud/frontier one. <https://nvd.nist.gov/vuln/detail/CVE-2025-32711>

---

## Routing Axes

| Axis | Local favoured | Frontier favoured | Human required |
|------|---------------|-------------------|----------------|
| **Sensitivity** | Internal logs, hostnames, usernames, unredacted alerts | Scrubbed/anonymised data | PII, PCI-in-scope data, attorney-client material |
| **Latency tolerance** | < 5 seconds acceptable | Minutes acceptable | Human SLA defines it |
| **Reasoning complexity** | Pattern match, classification, extraction | Cross-domain synthesis, legal reasoning, novel threat | Irreversible consequence, high-stakes judgment |

---

## Completed examples

| Task | Sensitivity | Latency tolerance | Complexity | **Routing** | Rationale |
|------|------------|------------------|------------|-------------|-----------|
| Classify an alert as true positive / false positive (internal log data) | High — contains hostnames, usernames | Low (< 3 s) | Medium | **Local** | Internal data cannot leave the perimeter — sending it to a cloud model is the LLM06 exposure EchoLeak (CVE-2025-32711) weaponised; classification is a pattern-match the small model handles well |
| Draft a post-incident executive summary (scrubbed incident timeline) | Medium — scrubbed | High (minutes OK) | High | **Frontier** | Scrubbed data is safe to send; executive summary requires coherent long-form reasoning a small model struggles with |
| Approve a customer-facing answer about policy/eligibility | Low data sensitivity | High | High — legal, reputational | **Human** | Moffatt v. Air Canada: the org is liable for a confident-but-wrong AI answer to a customer; a human verifies any externally-binding statement before it ships |
| Recommend whether to pay a ransomware demand | Low data sensitivity | High | Very high — legal, ethical, reputational | **Human** | Irreversible financial and legal consequence; AI prepares the briefing, a human and legal counsel decide |
| Extract IOCs (IPs, hashes, domains) from a raw log line | High | Low | Low | **Local** | Structured extraction from a fixed format; no reasoning depth required; keep internal log data on-prem (LLM06) |
| Summarise a public threat intel report (public URL, no internal data) | None | High | Medium | **Frontier** | No sensitive data involved; frontier model produces higher-quality summaries of long documents |

---

## Your turn — complete these five rows

Fill in **Sensitivity**, **Latency tolerance**, **Complexity**, **Routing decision**, and
a **one-sentence rationale** for each task below.

| Task | Sensitivity | Latency tolerance | Complexity | **Routing** | Rationale |
|------|------------|------------------|------------|-------------|-----------|
| Suggest a SIEM search query given a verbal description of suspicious behaviour | | | | | |
| Triage a phishing email (full headers and body from internal mailbox) | | | | | |
| Generate a draft firewall rule from a change request ticket | | | | | |
| Identify whether a binary hash appears in a threat feed (lookup, not analysis) | | | | | |
| Write a root-cause analysis for a confirmed incident (contains customer account IDs) | | | | | |

---

## OWASP LLM reference

Cite the relevant OWASP LLM risk in your `routing-policy.md`. Key risks for routing decisions:

- **LLM06 — Sensitive Information Disclosure**: model outputs or API calls expose data the
  application should not reveal (or transmit). Routing internal alert data to a cloud model
  is an LLM06 exposure — EchoLeak (CVE-2025-32711) is the real-world proof: data pulled into a
  cloud model's context was exfiltrated with zero clicks.
- **LLM09 — Overreliance**: treating model output as authoritative rather than as a draft for
  human review. Applies whenever a model output triggers an irreversible action.
- **LLM02 — Insecure Output Handling**: model output consumed without validation (e.g., a
  generated firewall rule applied without review). Applies to "Frontier / Human" tasks.

---

*This matrix is a living document. Update it as you discover new task categories or as model
capability changes. Version it in git.*
