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
- [ ] `data/eval-set.json` holds a labeled `query → expected-doc` set including a not-in-corpus / should-abstain case (`expected: null`).
- [ ] `make eval` runs `scripts/eval_rag.py` and reports **retrieval@k** plus a **grounding flag** per query, and exits non-zero when retrieval@k falls below your threshold (or the should-abstain case answers anyway).

## Deliverables
`data/knowledge-base/<your-runbook>.md` + `results/rag-evaluation.md` + `data/eval-set.json` +
`scripts/eval_rag.py` (and the `make eval` output). Commit all of them. The knowledge base additions
are the corpus Meridian's copilot will use in Module 06; the eval set + harness are how you prove
retrieval works rather than eyeballing it.

## Automate & own it
**Required — build an eval harness, don't eyeball retrieval.** Step 3 judged relevance by eye;
that doesn't scale and isn't reproducible. Turn it into a measured gate:

1. Write a small labeled set `data/eval-set.json` — a handful of `query → expected source-doc`
   pairs covering the knowledge base, **including at least one not-in-corpus / should-abstain case**
   (a query whose `expected` is `null`, where the right behaviour is "no relevant doc / I don't know").
2. Write `scripts/eval_rag.py` that runs each query through the pipeline and reports, per query and
   in aggregate:
   - **retrieval@k** — did the expected source doc appear in the top-k retrieved chunks? (and for the
     not-in-corpus case, that nothing was wrongly retrieved / the model abstained)
   - a **grounding flag** — does the generated answer assert a fact that is *not* present in the
     retrieved chunks? (a simple heuristic is fine: flag answer sentences with no supporting chunk)
3. Wire it to a `make eval` target that prints the scores and **exits non-zero when retrieval@k
   falls below your threshold** (or the should-abstain case answers anyway).

Have a model draft the scoring loop; **you** own the labeled set and the threshold, and you verify the
grounding heuristic against the raw chunks before trusting it. Commit `data/eval-set.json`,
`scripts/eval_rag.py`, and the `make eval` output.

> Note: `make eval` needs a Docker + model re-validation pass (Ollama `tinyllama` + `nomic-embed`
> pulls) before it counts as run — it rests on the already-validated three-container env but the new
> target has not yet been executed here.

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
