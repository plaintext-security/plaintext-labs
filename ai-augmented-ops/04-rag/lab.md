# Lab 04 — Retrieval-Augmented Generation

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/04-rag
make up && make demo
```

**Requirements:** Docker, 6 GB RAM free. No GPU needed.
Three containers start: Ollama (generation), ChromaDB (vector store), and a lab container
with the ingestion and query scripts. First run downloads `tinyllama` (~637 MB) and
`nomic-embed-text` (~274 MB). `make demo` ingests the knowledge base, runs one query,
and shows the retrieved chunks alongside the generated answer.

## Scenario
Meridian's security team maintains a knowledge base of runbooks, past incident summaries,
and detection notes. During an incident, analysts waste time searching Confluence for
the right runbook. Your job: build a RAG pipeline that lets an analyst ask a natural-language
question and get an answer grounded in Meridian's actual documents — not the model's training data.

> Everything runs locally. No cloud API keys required.

## Do

1. [ ] `make demo` and read the full output carefully. Find:
   - The **retrieved chunks**: which documents did the retrieval step return?
   - The **generated answer**: what did the model produce?
   - Are there any facts in the answer that aren't in the retrieved chunks? (hallucination-on-context)

2. [ ] `make shell` and open `scripts/ingest.py`. Read the chunking logic: what is the
   chunk size in characters? What is the overlap? In `data/knowledge-base/`, which document
   is longest? Would a 500-character chunk capture a complete procedure step from that document?
   Adjust `CHUNK_SIZE` if it doesn't.

3. [ ] Run three more queries against the knowledge base using `scripts/query.py`:
   ```bash
   python3 scripts/query.py "What is the escalation path for a confirmed ransomware event?"
   python3 scripts/query.py "Which detection rule covers lateral movement via PsExec?"
   python3 scripts/query.py "How long does Meridian retain network flow logs?"
   ```
   For each, note: were the retrieved chunks relevant? Did the answer accurately reflect
   them? Record your observations in `results/rag-evaluation.md`.

4. [ ] Deliberately break retrieval: run a query for something not in the knowledge base:
   ```bash
   python3 scripts/query.py "What is Meridian's policy on cryptocurrency payments?"
   ```
   What does the model return when retrieval finds nothing relevant? Document the behaviour.

5. [ ] Add one document to `data/knowledge-base/` — write a short (150–300 word) fictional
   Meridian runbook for a topic not already covered (e.g. "Insider threat containment procedure").
   Re-ingest (`make ingest`), then query for it. Does retrieval find it?

## Success criteria — you're done when
- [ ] `make demo` runs to completion and prints retrieved chunks + a generated answer.
- [ ] `results/rag-evaluation.md` has observations for all three additional queries in step 3.
- [ ] The "nothing in corpus" behaviour is documented.
- [ ] Your new document is in `data/knowledge-base/`, ingested, and retrievable by query.

## Deliverables
`data/knowledge-base/<your-runbook>.md` + `results/rag-evaluation.md`. Commit both.
The knowledge base additions are the corpus Meridian's copilot will use in Module 06.

## Automate & own it
**Required.** Extend `scripts/ingest.py` to support incremental ingestion: check whether
a document's filename already exists in the ChromaDB collection before re-embedding it,
and skip it if so. Have a model draft the ID-based deduplication logic; you verify it
handles the case where the document content changed but the filename didn't (it should
re-embed in that case). Run `make ingest` twice and confirm the second run skips documents
already in the store. Commit the updated script.

## AI acceleration
Paste the ChromaDB query results (the raw retrieved chunk text) into a frontier model and
ask it to identify retrieval gaps: "Given these chunks, what question could I ask that
would be poorly answered because the corpus doesn't cover it?" The exercise surfaces
knowledge base gaps before you hit them during an incident.

## Connects forward
The ingested ChromaDB collection from this module is the retrieval backend for the
SoC Copilot in Module 06. Module 09 attacks this pipeline: a document injected into the
knowledge base can poison retrieval and manipulate model answers.

## Marketable proof
> "I can build a RAG pipeline grounded in a private corpus — embedding with nomic-embed,
> storing in ChromaDB, generating with Ollama — and I can identify retrieval failure modes
> before they reach production."

## Stretch
- Implement hybrid search: combine ChromaDB vector similarity with a keyword filter
  (e.g. require the retrieved chunks to contain the exact phrase the analyst used).
  Compare precision vs. recall for the same queries.
- Add a "source citation" step: modify the query prompt to require the model to cite the
  document filename for every factual claim in its answer. Verify the citations are accurate.
