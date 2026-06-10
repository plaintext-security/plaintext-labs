# Module 06 — A SoC Copilot (MCP + RAG)

*Module concept · [Go to the hands-on lab →](lab.md)*


**AI-Augmented Security Operations** — *the copilot combines everything: institutional memory from RAG, live data from MCP tools, and reasoning from the local model.*

## Why this matters
Modules 04 and 05 built the two halves of a useful AI assistant: a knowledge base that can be
queried for institutional context, and a set of tools that can pull live data. This module
combines them into a working SoC copilot — a service that accepts a natural-language question,
decides what context to retrieve and what tools to call, and produces a structured answer that
a SOC analyst can act on. This is the architecture that makes AI operationally useful in a
security context rather than merely impressive in a demo.

## Objective
Deploy the three-container copilot stack (Ollama + ChromaDB + copilot app), ask it a realistic
SOC question, and trace the full reasoning chain — retrieval, tool call, generation — from input
to output.

## The core idea
The copilot architecture is a coordination layer, not a new kind of model. When a question
arrives, the copilot does three things in sequence: it queries ChromaDB for the N closest
knowledge-base chunks (what do Meridian's own documents say about this?), calls the relevant
MCP tools for live data (what does the threat intel database say about this IOC right now?),
and then constructs a prompt that injects both the retrieved context and the tool results before
asking the generation model for a final answer. The model sees everything at once: historical
runbooks, live intel, and the question. It reasons across all of it.

The sophistication is in the coordination logic, not the model. A naive implementation sends
all retrieved chunks and all tool results into the prompt and hopes for the best. A production
implementation is selective: it only retrieves context relevant to the question, it only calls
tools that are likely to have useful data (why call `get_threat_intel` for an IOC that's clearly
an internal hostname?), and it structures the prompt so that the model knows which parts of
the context are from authoritative documents vs. live lookups vs. its own training data. The
copilot's prompt engineering is where most of the actual quality difference lives.

Trust boundaries don't disappear in the copilot architecture — they multiply. The model now
has access to both RAG context and tool results simultaneously, which creates a compound attack
surface: an adversary can try to manipulate the copilot by injecting content into the knowledge
base (context poisoning), by crafting an IOC that returns a manipulative threat intel record
(tool result poisoning), or by embedding instructions in an alert that tell the model to ignore
its system prompt (prompt injection via tool output). All three of these are real techniques
against this architecture, and Module 09 demonstrates each one. Building the copilot first lets
you understand what you're attacking before you attack it.

One operational discipline that separates a useful copilot from a dangerous one: the copilot
should always show its work. Meridian's copilot prints the retrieved chunks and tool call results
alongside the generated answer — the analyst can see exactly what evidence the model used. An
answer that cites three retrieved chunks and a threat intel record is auditable; an answer that
just says "this looks malicious" is not. Transparency is not a UI nicety; it's the mechanism by
which the "AI authors → you review → you own it" discipline becomes possible.

## Learn (~2 hrs)

**Putting it together (~1 hr)**
- Review Modules 04 (RAG) and 05 (MCP Servers) before this module — you'll be combining both.
- [LangGraph — "Agentic RAG" conceptual overview](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag/) — an example of exactly this pattern (retrieve + tool call + generate) in a graph-based agent framework. Skim for the architecture, not the API.

**Prompt design for copilots (~30 min)**
- [Anthropic, "Give Claude a role with a system prompt" (Docs)](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) — the system prompt engineering section is model-agnostic; the principles apply to any copilot system prompt, including Ollama-served models.

**Attack surface (~30 min)**

## Key concepts
- Copilot as a coordination layer: retrieve → call tools → generate — in that order
- Selective retrieval and tool calling vs. "stuff everything into context"
- Trust boundary multiplication in combined RAG + MCP architectures
- Transparency as auditability: showing the evidence chain alongside the answer
- Prompt injection via tool output: why tool results must be treated as untrusted input

## AI acceleration
Have a model help draft the coordination logic — the function that decides which tools to call
based on the question content (does it mention an IP or domain? call threat intel; does it
mention a procedure? rely on RAG). Review the decision logic: does it miss cases? Does it call
tools unnecessarily? The model writes the heuristic; you test it against edge cases.
