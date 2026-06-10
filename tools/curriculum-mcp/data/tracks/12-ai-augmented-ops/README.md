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

## Prerequisites
Complete Track 00 — Foundations; Track 09 — Python is strongly recommended.

> Test prompt-injection and jailbreak techniques only against models and applications you
> own or are authorised to assess.

## Capstone
Build a small SoC copilot — an MCP server exposing one real tool, grounded in a RAG corpus
of your own notes — then red-team it: demonstrate a prompt-injection or data-exfil weakness
and harden against it. **Deliverable:** the copilot, the attack, and the fix.

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
