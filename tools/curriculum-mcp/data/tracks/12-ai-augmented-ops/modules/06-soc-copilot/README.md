# Module 06 — A SoC Copilot (MCP + RAG)

*Type 7 · Build-&-Operate — integrate RAG + MCP + a local model into an auditable SOC copilot and score it end-to-end; the deliverable is the running copilot and its answer-quality scorecard. (Secondary: Eval Harness.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**AI-Augmented Security Operations** — *the flagship system gets a scorecard, not vibes: the most consequential thing you built is the one you've measured least.*

<!-- module-meta -->
**Difficulty:** Advanced &nbsp;·&nbsp; **Estimated time:** ~5–7 hrs (study + lab) &nbsp;·&nbsp; **Type:** Build-&-Operate + Eval Harness (end-to-end) &nbsp;·&nbsp; **Prerequisites:** [04 — RAG](../04-rag/README.md), [05 — Building MCP Servers](../05-building-mcp-servers/README.md), [07 — AI Detection & Triage](../07-ai-detection-triage/README.md), [11 — AI Evaluation & Observability](../11-ai-evaluation/README.md)
{ .module-meta }

## Why this matters
Modules 04 and 05 built the two halves of a useful AI assistant: a knowledge base you can query for
institutional context, and a set of tools that pull live data. This module combines them into a
working SoC copilot — a service that takes a natural-language question, decides what to retrieve and
which tools to call, and produces a structured, **auditable** answer an analyst can act on. It is the
architecture that makes AI operationally useful in a SOC rather than merely impressive in a demo, and
it is the capstone target for this track.

It is also, by the type pass's own diagnosis, the single most dangerous thing in the curriculum to
ship on vibes. **The most consequential system you build is the one you've evaluated least.** The
copilot compounds three independent failure surfaces — retrieval can miss, the tool router can fire
the wrong tool, and the model can hallucinate over both — and every one of those failures arrives
wrapped in the same fluent, confident paragraph. A RAG-only system you can eyeball; a copilot that
answers "escalate this to your IR lead, no open incident exists" when an incident *is* open, because
it never called the right tool, is a system that fails silently with authority. This module finishes
the copilot and then does the thing teams skip: it builds the **end-to-end scorecard** — answer
quality *plus* retrieval relevance *plus* tool-selection correctness — over a held-out set of SOC
questions, so the flagship system is the *best*-measured one, not the worst.

## Objective
Deploy the three-container copilot stack (Ollama + ChromaDB + copilot app) and confirm it answers a
realistic SOC question with a full, traceable reasoning chain — then build the **end-to-end eval**
that scores it: a held-out question set graded on three axes (tool-selection correctness via a
confusion matrix, retrieval relevance via recall@k, and answer groundedness), written to a
**scorecard** and wired to a **regression gate**, all plugging into Module 11's harness.

## The core idea
The copilot is a **coordination layer**, not a new kind of model. When a question arrives it does
three things in sequence: it queries ChromaDB for the closest knowledge-base chunks (*what do our own
documents say about this?*), it calls the relevant tools for live data (*what does the threat-intel
DB say about this IOC right now? is there an open incident on this host?*), and it constructs a prompt
that injects both the retrieved context and the tool results before asking the generation model for a
final answer. The model sees historical runbooks, live data, and the question at once, and reasons
across all of it. The sophistication lives in the coordination, not the weights: a good copilot
retrieves *selectively*, calls only the tools likely to have useful data (don't `get_threat_intel` an
internal hostname), and structures the prompt so the model knows which facts are authoritative
documents, which are live lookups, and which are its own priors. And it **shows its work** — it prints
the retrieved chunks and the tool calls alongside the answer, so an analyst can see exactly what
evidence the model used. An answer that cites three chunks and a threat-intel record is auditable; one
that just says "this looks malicious" is not. That transparency is the mechanism that makes "AI
authors → you review → you own it" possible at all — and, not coincidentally, it is what makes the
copilot *evaluable*.

The one load-bearing judgment of this module is that **a system that compounds three components fails
in three independent ways, and a single answer-quality glance sees none of them cleanly.** This is the
exact trap Module 11 names — a non-deterministic system that performed on the handful of inputs you
tried is not measured, it is anecdotal — but the copilot raises the stakes, because the failure can
originate at any of three layers and the prose papers over all of them identically. So the deliverable
is not "a copilot that answered my demo question." It is the copilot **plus** an end-to-end scorecard
that decomposes the failure by layer:

- **Tool-selection correctness** — for each held-out question, did the router call the tools it
  *should* have (and not the ones it shouldn't)? This is a classification problem, scored with the
  exact confusion-matrix discipline of Module 07: per-tool precision and recall over the labelled
  set, so a router that quietly stops calling `summarize_incident` shows up as a recall collapse on
  that tool rather than as a vaguely-worse vibe. The asymmetry from 07 carries over: a *missed* tool
  call (the open incident never surfaced) usually costs more than a spurious one.
- **Retrieval relevance** — did the right knowledge-base chunk land in the top-k? This is the
  **recall@k** check you built in Module 04, reused verbatim as the retrieval half of the copilot's
  score. The copilot retrieves from the *same* corpus, so the same labelled query set and the same
  metric apply; you are not reinventing it, you are plugging it in.
- **Answer groundedness** — are the answer's claims actually supported by the retrieved chunks and
  tool results it was given, or did the model fabricate over good evidence? Same minimal
  span-overlap groundedness as Module 04, now measured against *both* RAG context and tool output,
  because in a copilot the model can hallucinate over a perfectly correct tool result too.

Three numbers, one held-out set, graded against data the copilot was never tuned on — and a
**regression gate** so a future "harmless" change (a new system prompt, a tweaked tool heuristic, a
re-quantised model) has to prove it didn't tank any of the three before it merges. The point is not
that the copilot scores perfectly — a `tinyllama`-class local model will not — but that its
performance is **known, decomposed, and gated** instead of admired. Trust boundaries don't disappear
in this architecture either; they multiply (context poisoning, tool-result poisoning, prompt
injection via tool output are all real against this stack), which is exactly why Module 09 attacks the
copilot you build here — and why the eval you build here becomes the regression test that proves a
mitigation holds.

## Learn (~2.5 hrs)

**Putting it together (~1 hr)**
- Review Modules [04 (RAG)](../04-rag/README.md) and [05 (MCP Servers)](../05-building-mcp-servers/README.md) — you are combining both; the retrieval eval and the tool tests you built there are the two halves you reuse here.
- [LangGraph — "Agentic RAG" conceptual overview](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag/) — a worked example of exactly this retrieve → tool-call → generate pattern in a graph-based agent framework. Skim for the architecture and the routing decision, not the API.

**Prompt design & provenance (~30 min)**
- [Anthropic — "System prompts"](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/system-prompts) — model-agnostic guidance on giving the assistant a role and grounding rules; the principles (state the role, constrain to provided evidence, demand citations) apply to any copilot system prompt, including an Ollama-served local model. Read it for the "constrain the answer to the provided context" pattern your copilot's prompt enforces.

**Evaluating the whole system, not a layer (~1 hr)**
- [Module 11 — AI Evaluation & Observability](../11-ai-evaluation/README.md) — the shared held-out-set + scorecard + regression-gate harness this module's end-to-end eval plugs into. Re-read "The core idea": this copilot is the system that module warns is currently the *least* measured.
- [Anthropic — "Define success criteria and build evaluations"](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests) — first-party guidance on building task-specific eval sets and choosing graders (exact-match vs. model-graded), and the held-out discipline; vendor-neutral on the principles, and the right framing for a multi-axis eval where each axis needs a *different* grader.
- [RAGAS docs — "Metrics" overview](https://docs.ragas.io/en/stable/concepts/metrics/) — the standard vocabulary for the retrieval and groundedness halves (context recall, faithfulness). You already reimplemented a minimal recall@k in Module 04; skim here for *why* an end-to-end RAG-plus-tools system needs retrieval *and* groundedness scored separately.

## Key concepts
- The copilot is a coordination layer: retrieve → call tools → generate, in that order; the quality lives in *selective* retrieval and routing, not the model.
- Transparency = auditability: show the retrieved chunks and tool calls alongside the answer, or "AI authors → you review → you own it" is impossible — and so is evaluating it.
- The flagship system is the least-evaluated one: a system that compounds three components fails three independent ways, all hidden under one fluent paragraph.
- **Tool-selection correctness** is a classification problem — score it with Module 07's confusion matrix (per-tool precision/recall); a missed tool call costs more than a spurious one.
- **Retrieval relevance** is Module 04's recall@k, reused verbatim over the same corpus; **groundedness** now spans both RAG context *and* tool results.
- One held-out question set, three scores, a regression gate — plugged into Module 11. The point is *known and gated*, not *perfect*.

## AI acceleration
A model writes the mechanical parts of the eval well — iterating the held-out questions, tabulating
the per-tool confusion matrix, computing recall@k and span-overlap groundedness, formatting the
scorecard, parsing the predictions log. **What you must own is everything a model will quietly get
wrong on a multi-axis eval.** First, the **labels**: the "expected tools" for each question and the
"relevant chunk" for each query are *your* judgments against the source data — a model labelling its
own copilot's answer key is the contamination Module 11 exists to prevent, so it may *draft* candidate
questions but you confirm the ground truth. Second, the **per-axis grader and direction**: tool
selection wants recall-weighted scoring (a missed `summarize_incident` is the costly error), retrieval
wants recall@k, groundedness wants span overlap — defaulting all three to "accuracy" hides the failure
that matters, and the gate must **fail closed** (a missing axis, an errored eval, or a copilot that
crashed must turn the build red, never silently pass). Third, the **held-out wall**: a model will
happily score against the demo question; the whole point is grading questions the copilot was never
tuned against. The model writes the arithmetic; you own the labels, the three metrics, and the gate.
