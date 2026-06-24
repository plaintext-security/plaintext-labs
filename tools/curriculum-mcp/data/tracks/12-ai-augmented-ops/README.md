# Track 12 — AI-Augmented Security Operations

**The force multiplier — and the new attack surface.** Run your own models, ground them in
your data, wire them to your tools, and automate the boring 80% — then learn to secure and
attack the AI systems you just built.

## What you'll be able to do
- Run local models and know when to reach for a frontier model instead.
- Ground answers in your own corpus with RAG.
- Expose security tools to an LLM via MCP and build a working SoC copilot.
- Attack and harden AI/MCP/RAG systems.

## Modules

| # | Module | What you'll learn | OSS tools |
|---|--------|-------------------|-----------|
| 01 | [The Hybrid AI Pattern](modules/01-hybrid-ai-pattern/README.md) | Local vs frontier: what runs where, and why | `ollama` |
| 02 | [Running Local Models](modules/02-running-local-models/README.md) | Serving models on modest hardware | `ollama`, `llama.cpp` |
| 03 | [Prompt Patterns for Security](modules/03-prompt-patterns/README.md) | Reliable, reviewable prompting | — |
| 04 | [Retrieval-Augmented Generation](modules/04-rag/README.md) | Grounding answers in your corpus | `chromadb`, `nomic-embed` |
| 05 | [Building MCP Servers](modules/05-building-mcp-servers/README.md) | Exposing security tools to an LLM | `fastmcp` |
| 06 | [A SoC Copilot (MCP + RAG)](modules/06-soc-copilot/README.md) | An assistant grounded in your data and tools | `fastmcp`, `chromadb` |
| 07 | [AI-Assisted Detection & Triage](modules/07-ai-detection-triage/README.md) | Local models for cheap, high-volume triage | `ollama` |
| 08 | [SOAR + AI](modules/08-soar-ai/README.md) | Automated response with a human in the loop | `Shuffle` |
| 09 | [Securing the AI You Run](modules/09-securing-ai/README.md) | Prompt injection, data exfil, MCP/RAG hardening | — |
| 10 | [Attacking AI Systems](modules/10-attacking-ai/README.md) | Red-teaming LLM/MCP/RAG applications | `garak`, `promptfoo` |
| 11 | [AI Evaluation & Observability](modules/11-ai-evaluation/README.md) | Held-out evals, regression gates, observability — eval gates, not vibes | `pytest`, `promptfoo` |

## Phases & projects

The ten modules run in three phases; each ends in a **project** that integrates its modules (a phase
is the substantial, standalone unit — a single module is a few hours).

- **Phase 1 · Run & ground models** (01–04) — **Project:** a local-model setup (Ollama/llama.cpp)
  with a reviewable prompt library and a working RAG pipeline that grounds answers in your own
  security notes — proving when local suffices and when a frontier model earns the call.
- **Phase 2 · Build the copilot** (05–08) — **Project:** an MCP server exposing one real security
  tool, wired to the RAG corpus into a SoC copilot that triages at volume, plus a SOAR + AI playbook
  that drafts a response and waits for human approval.
- **Phase 3 · Secure & attack the AI** (09–10) — **Project:** the track capstone — red-team the
  copilot you built: demonstrate a prompt-injection or data-exfil weakness with `garak`/`promptfoo`,
  then harden against it — delivering the copilot, the attack, and the fix.

## Prerequisites
Complete Track 00 — Foundations; Track 09 — Python is strongly recommended.

> Test prompt-injection and jailbreak techniques only against models and applications you
> own or are authorised to assess.

## Capstone
Build a small SoC copilot — an MCP server exposing one real tool, grounded in a RAG corpus
of your own notes — then red-team it: demonstrate a prompt-injection or data-exfil weakness
and harden against it. **Deliverable:** the copilot, the attack, and the fix.

The starter scaffold and acceptance checks live in
[`plaintext-labs/ai-augmented-ops/capstone/`](https://github.com/plaintext-security/plaintext-labs/tree/main/ai-augmented-ops/capstone).

### Capstone rubric

You **build the copilot, break it, then fix it** — and the fix must hold against the attack you
showed. **Proficient is the bar to ship.**

| Dimension | Developing | Proficient | Exemplary |
|---|---|---|---|
| **The copilot** | Bare LLM call, no grounding or tools | MCP server exposing one real tool, grounded in a RAG corpus of your notes | Genuinely useful for a SOC task; retrieval is relevant and tools are scoped |
| **The attack** | Theoretical, not demonstrated | A working prompt-injection or data-exfil exploit shown against your own system | Mapped to OWASP LLM Top 10 / MITRE ATLAS; shows real impact (tool misuse or data leak) |
| **The fix** | Generic advice, not applied | A concrete hardening that defeats the demonstrated attack | Re-tested: the same attack now fails; defence-in-depth (input + tool-scoping + output checks) |
| **Tool & data scoping** | Tools/over-broad access unbounded | Tools and retrieval scoped to least privilege | Untrusted content can't reach privileged tools; the trust boundary is explicit |
| **Write-up** | Disconnected pieces | Build → attack → fix told as one coherent story | Honest about residual risk and what the model can still be tricked into |

## AI & automation
This track *is* the AI thesis made explicit, and it closes the loop the whole curriculum
runs on: you build the automation, then you attack it. The discipline throughout —
*AI authors → you review → you own it* — applies hardest here, because the thing reviewing
the output is also the thing under test.

## Standards & further reading
- OWASP Top 10 for LLM Applications
- MITRE ATLAS (adversarial threats to AI systems)
- NIST AI Risk Management Framework (AI RMF)
- The Model Context Protocol specification (modelcontextprotocol.io)
