# Runbook — Responding to an LLM prompt-injection

**Class:** Prompt injection (OWASP LLM Top 10 — LLM01). **Severity:** depends on what the model can
*do* (read-only chat vs. tool-calling agent with privileged tools).

## The two shapes, with named precedents
- **Direct injection / jailbreak** — a user instructs the model to ignore its rules. *Precedent:*
  the **Chevrolet of Watsonville** chatbot (Dec 2023) was told to "agree with everything the
  customer says" and ended up "agreeing" to sell a 2024 Tahoe for **$1**. No business-logic
  guardrail behind the prose. <https://github.com/vectara/awesome-agent-failures/blob/main/docs/case-studies/chevrolet-dealership-chatbot.md>
- **Indirect injection** — the malicious instruction is hidden in *content the model retrieves*
  (a document, an email, a tool description), not typed by the user. *Precedent:* **EchoLeak,
  CVE-2025-32711** — a zero-click indirect injection in Microsoft 365 Copilot that exfiltrated
  sensitive context data the model had pulled in via RAG (LLM01 + LLM06).
  <https://nvd.nist.gov/vuln/detail/CVE-2025-32711> See also Invariant Labs' MCP tool-poisoning
  disclosure (hidden instructions in *tool descriptions*):
  <https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks>

## Why it matters even when the model "is just answering"
An organisation owns its AI's output. In **Moffatt v. Air Canada (2024 BCCRT 149)** the airline was
held liable for a wrong answer its chatbot gave a customer — the tribunal rejected "the bot is a
separate entity." Treat model output reaching a user or a tool as the org's own statement/action.

## Response & hardening (defence-in-depth, not one filter)
1. **Input** — separate trusted instructions from untrusted content; never concatenate retrieved
   text into the instruction position.
2. **Tool-scoping** — least privilege: untrusted content must not be able to reach a privileged tool
   (the trust boundary must be explicit). This is the control that contains EchoLeak-class exfil.
3. **Output** — validate/allowlist what the model can emit or trigger; gate irreversible actions
   behind a human (LLM09 — Overreliance).
4. **Re-test** — replay the exact injection and confirm it now fails; a fix you didn't re-test is a
   wish.
