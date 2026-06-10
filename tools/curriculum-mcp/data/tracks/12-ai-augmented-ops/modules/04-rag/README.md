# Module 04 — Retrieval-Augmented Generation

*Module concept · [Go to the hands-on lab →](lab.md)*


**AI-Augmented Security Operations** — *a model without your data is answering from memory; RAG is how you give it the right context.*

## Why this matters
A base language model knows only what was in its training data, which stops at a cutoff date and
contains nothing proprietary — no Meridian's runbooks, no past incident timelines, no internal
detection notes. RAG (Retrieval-Augmented Generation) is the standard pattern for grounding model
answers in a specific corpus: embed your documents into a vector store, embed the user's query into
the same space, retrieve the semantically closest chunks, and stuff them into the model's context
window alongside the question. The result is a model that can answer "What was the containment
procedure for the 2024 Meridian credential incident?" from your actual post-incident report, not
from its training priors.

## Objective
Build a working RAG pipeline against a fictional Meridian security knowledge base, query it with
realistic SOC questions, and document where retrieval succeeds and where it fails — and why.

## The core idea
The intuition behind vector search is simpler than the term suggests: encode every document chunk
as a list of numbers (a vector embedding) that represents its meaning in high-dimensional space.
Semantically similar text produces vectors that are close together by cosine distance. When a query
arrives, embed it the same way and find the N nearest document chunks — those are the most
semantically relevant passages, regardless of whether they share keywords with the query. This is
why RAG retrieves "The containment procedure for account compromise" when asked "What do I do when
a credential is stolen?" even if the document never uses the word "stolen."

The embedding model is a distinct component from the generation model. `nomic-embed-text` is a
purpose-built, small (137M parameter) embedding model that converts text chunks to 768-dimensional
vectors without being a generative model at all — it doesn't produce language, only representations.
ChromaDB stores those vectors and performs the nearest-neighbour search efficiently. Ollama serves
the generation model that takes the retrieved chunks and answers the question. These three
components are independently swappable: change ChromaDB to Qdrant, or swap `nomic-embed-text` for
`all-minilm`, and the rest of the pipeline doesn't change.

The failure modes of RAG are different from the failure modes of raw generation. **Retrieval
misses** (the relevant document exists but the retrieved chunks don't contain it) happen when your
chunk size doesn't bracket the relevant passage, when the embedding model doesn't represent your
domain vocabulary well, or when the query is phrased in a way that doesn't match the document.
**Context poisoning** (retrieved chunks that contradict each other or include outdated information)
happens when your corpus isn't curated — stale runbooks and superseded procedures surface alongside
current ones. **Hallucination-on-context** (the model fabricates details that aren't in the
retrieved chunks) is less common than pure generation hallucination but still happens, especially
with small models. The discipline of reviewing retrieved chunks before trusting the answer is
non-negotiable.

For a security team, RAG is most useful for read-heavy tasks on a stable corpus: querying past
incident summaries, surfacing relevant runbook steps, finding precedent for a detection rule.
It's less useful for tasks requiring real-time data (threat feeds, current CVEs) — those require
tool calls, not retrieval (Module 05). The architecture at Meridian keeps them separate: RAG for
institutional knowledge, MCP tools for live data, and the model generates the final answer from
both. That combination is Module 06.

## Learn (~3 hrs)

**How RAG works (~1.5 hrs)**
- [LlamaIndex — "What is RAG?" explainer](https://developers.llamaindex.ai/python/framework/getting_started/concepts/) — the cleanest conceptual walkthrough: retrieval, augmentation, generation in sequence; read the "Key concepts" page.
- [ChromaDB documentation — Getting started](https://docs.trychroma.com/docs/overview/getting-started) — the vector store you'll use; skim the basic collection, add, and query examples before touching the lab.

**Chunking and retrieval quality (~1 hr)**
- [Greg Kamradt, "5 Levels of Text Splitting" (YouTube, 25 min)](https://www.youtube.com/watch?v=8OJC21T2SL4) — the most practical treatment of chunking strategy; watch for the intuition on how chunk size affects retrieval precision vs. recall.
- [Jerry Liu, "Building Production-Ready RAG Applications" (YouTube, 45 min)](https://www.youtube.com/watch?v=TRjq7t2Ms5I) — covers the common failure modes (retrieval miss, hallucination-on-context) with concrete examples from production deployments.

**Security-specific considerations (~30 min)**
- [OWASP Top 10 for LLM — LLM08 (Excessive Agency) and LLM10 (Model Theft)](https://owasp.org/www-project-top-10-for-large-language-model-applications/) — retrieval pipelines that ingest external content introduce context-poisoning and data-exfil risks; understand these before Module 09.

## Key concepts
- Embedding as semantic proximity: vectors close in space, semantically similar in meaning
- Embedding model (nomic-embed) vs. generation model (Ollama/tinyllama): two distinct roles
- Chunk size tradeoffs: small chunks = precise retrieval, may miss full context; large = vice versa
- RAG failure modes: retrieval miss, context poisoning, hallucination-on-context
- RAG vs. tool calls: static corpus retrieval vs. live data (covered in Module 05)

## AI acceleration
Use a model to help draft the corpus ingestion script — it knows the ChromaDB API well and
can write the chunk-split-embed-store loop in seconds. Your job is to review the chunking
logic (is the split size appropriate for the document lengths in your knowledge base?) and
the query prompt (is the retrieved context injected into the prompt in a position where the
model can actually use it?). The model writes the boilerplate; you own the architecture.
