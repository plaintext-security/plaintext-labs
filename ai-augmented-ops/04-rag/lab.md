# Lab 04 — RAG, and the retrieval eval that keeps it honest

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/04-rag
make up && make demo
```

**Requirements:** Docker, 6 GB RAM free. No GPU needed.
Three containers start: Ollama (generation), ChromaDB (vector store), and a lab container with the
ingest, query, and eval scripts. First run downloads `tinyllama` (~637 MB) and `nomic-embed-text`
(~274 MB). `make demo` ingests the knowledge base, runs one query, shows the retrieved chunks
alongside the generated answer — **and then runs the retrieval eval over the labelled query set and
prints the scorecard**, so you see the build and its measurement in one pass.

> The retrieval eval (`make eval`) scores recorded retrievals against a committed labelled query set.
> Once ingested, that scoring is deterministic and needs no live generation — the same offline,
> CI-friendly discipline as Module 11.

## Scenario
A security team maintains a knowledge base of runbooks, past incident summaries, and detection notes.
During an incident, analysts waste time hunting the right runbook in the wiki. You build a RAG
pipeline that answers a natural-language question from those actual documents — and then you do the
thing most teams skip: you **prove the retrieval works**. A confident answer over the wrong runbook
is worse than no answer; the eval is how you catch it before an analyst trusts it at 3 a.m.

> Everything runs locally. No cloud API keys, no external targets, no authorization needed.

## Do

### Part A — Build & operate the RAG

1. [ ] `make demo` and read the full output carefully. Find:
   - The **retrieved chunks**: which documents did the retrieval step return?
   - The **generated answer**: what did the model produce?
   - Any fact in the answer that is *not* in the retrieved chunks (hallucination-on-context).
   Write one sentence: judged by the prose alone, would you have noticed if the retrieval was wrong?

2. [ ] `make shell`, then open `scripts/ingest.py`. Read the chunking logic: what is `CHUNK_SIZE`
   in characters, and the overlap? In `data/knowledge-base/`, which document is longest? Would the
   current chunk size capture a *complete* procedure step from that document? Note your reasoning —
   you'll measure the effect of this dial in Part B.

3. [ ] Run three more queries with `scripts/query.py` and eyeball relevance:
   ```bash
   python3 scripts/query.py "What is the escalation path for a confirmed ransomware event?"
   python3 scripts/query.py "Which detection rule covers lateral movement via PsExec?"
   python3 scripts/query.py "How long are network flow logs retained?"
   ```
   For each, were the retrieved chunks relevant, and did the answer reflect them? Then run a query
   for something **not** in the corpus and document what the model does when retrieval finds nothing:
   ```bash
   python3 scripts/query.py "What is the policy on cryptocurrency payments?"
   ```

### Part B — Build the retrieval eval (the deliverable)

4. [ ] **Read the labelled query set and understand *why* it's held out.**
   `data/eval-queries.json` maps ~15 realistic SOC questions to their **known-relevant** source
   document(s) — the answer key for retrieval. These queries are **separate from the demo question**
   and were never used to tune the chunking. Skim three: confirm each one's "relevant" doc is a
   *judgment about the source*, not a keyword match (e.g. a query about "a stolen password" should map
   to the credential-incident runbook even though it never says "stolen"). That semantic gap is
   exactly what recall@k tests.

5. [ ] **Score recall@k.** `make eval` embeds each labelled query, retrieves the top-k chunks, and
   checks whether at least one genuinely-relevant chunk appears — writing `results/retrieval-scorecard.md`
   with **recall@1 / @3 / @5** plus the per-query misses. Read it as a *number*, not a vibe. Which
   queries missed at k=3, and why — phrasing, chunk boundaries, or vocabulary?

6. [ ] **Score groundedness.** `make eval` also reports a minimal **groundedness** check on the
   generated answers (span overlap between the answer's claims and the retrieved chunks; an answer
   making claims absent from its context scores low). Find the query whose answer read most confidently
   but scored worst on groundedness — that gap is the silent failure the module is about. Note where
   simple span-overlap is too crude and would need an LLM-grader (and why that re-introduces the
   eval-the-evaluator problem).

7. [ ] **Prove the regression gate catches a real change.** `make gate` runs the eval with a declared
   floor (`recall_at_k=0.80`) and exits non-zero if retrieval drops below it. Now *cause* a
   regression: shrink the chunk size to a value too small to bracket a procedure step
   (`make ingest CHUNK_SIZE=120`), re-run `make gate`, and watch recall@3 collapse and the gate go
   **red (exit 1)**. Restore the good chunk size, re-ingest, and confirm the gate goes **green (exit
   0)**. The green-on-good / red-on-regression contrast is the whole point: a "harmless" chunking
   tweak can silently tank retrieval, and the gate is what stops it merging.

8. [ ] **Extend the held-out set with a hard case.** Add one document to `data/knowledge-base/`
   (a short 150–300-word runbook on a topic not yet covered — e.g. insider-threat containment),
   write **two labelled queries** for it in `data/eval-queries.json` (one phrased like the document,
   one phrased *unlike* it), re-ingest, and re-run `make eval`. Does retrieval find it on both? The
   phrased-unlike query is the one that exposes embedding/vocabulary gaps — exactly the case that
   "more easy queries" would never catch (coverage ≠ effectiveness).

## Success criteria — you're done when
- [ ] `make demo` runs to completion: retrieved chunks + generated answer + the retrieval scorecard.
- [ ] `make eval` produces `results/retrieval-scorecard.md` with recall@1/@3/@5 and a groundedness number, plus per-query misses.
- [ ] You can state, in writing, **why a RAG needs a *retrieval* metric and not just an "answer reads well" check** — and you've seen one confident answer score low on groundedness.
- [ ] `make gate` exits **0** on the good pipeline and **1** after `CHUNK_SIZE=120` — you've watched recall@3 collapse and recover.
- [ ] Your new document + its two labelled queries are committed, ingested, and scored.

## Deliverables
`data/eval-queries.json` (the labelled query set, including your two added queries) +
`scripts/eval.py` (with any metric/gate change you made) + `data/knowledge-base/<your-runbook>.md` +
`results/retrieval-scorecard.md`, all committed. **The eval-as-code is the artifact**: a labelled
held-out query set, a recall@k / groundedness scorecard, and a gate that fails on a retrieval
regression. Do **not** commit live run dumps (`results/predictions-*.json`, raw chunk text) — they're
gitignored and regenerate from the corpus + eval. The ingested collection + the corpus additions are
the retrieval backend the SoC copilot reuses in Module 06.

## Automate & own it
**Required.** Wire the retrieval gate into CI so a regression *cannot merge*. Add a
`.github/workflows/rag-eval.yml` (in your own portfolio repo) that, on every PR, ingests the corpus
and runs:
```
python3 scripts/eval.py --queries data/eval-queries.json --gate recall_at_k=0.80
```
Have a model draft the workflow YAML — it's boilerplate. **You own three things it will get wrong:**
(1) the gate must **fail closed** — if ingest fails, the eval errors, or the metric is missing, the
build fails; it does not silently pass (verify by running the gate with a typo'd metric name and
confirming a non-zero exit); (2) the threshold is a **recall floor**, not a "did it produce output"
check; (3) the queries fed to CI are the **held-out** labelled set, never the demo question. Commit
the workflow and a log of it going red on the `CHUNK_SIZE=120` regression.

## AI acceleration
Have a model **expand the labelled query set** — ask it for SOC questions phrased *unlike* the source
documents (the hard, vocabulary-gap cases recall@k is meant to catch) — then **label them yourself**:
open the source doc and confirm which chunk is genuinely relevant. A model labelling its own answer
key is the contamination Module 11 warns about; it proposes queries, you own the ground truth. Then
paste a low-groundedness answer plus its retrieved chunks into a frontier model and ask "which claims
here are *not* supported by this context?" — and check its verdict against the chunks yourself, because
trusting the grader uncritically is the same mistake one level up.

## Connects forward
The ingested collection and the retrieval eval both feed **Module 06**: the SoC copilot retrieves
from this corpus, and its end-to-end scorecard reuses this recall@k + groundedness check as the
retrieval half. **Module 11** is where this harness is generalised — same held-out + scorecard + gate
discipline, across triage and RAG together. **Module 09** attacks this pipeline: a document injected
into the knowledge base can poison retrieval and manipulate answers — and your retrieval eval becomes
the regression test that proves the poisoning stays fixed once you mitigate it.

## Marketable proof
> "I can build a RAG pipeline grounded in a private corpus — nomic-embed for embeddings, ChromaDB for
> the vector store, Ollama for generation — *and* I built the retrieval eval that proves it works: a
> labelled held-out query set, a recall@k and groundedness scorecard, and a CI gate that fails when a
> chunking or embedding change drops recall. I measure retrieval, I don't trust the prose."

## Stretch
- Add **hybrid search**: combine ChromaDB vector similarity with a keyword filter, then re-run
  `make eval` and report whether recall@k improved or regressed — let the number decide, not intuition.
- Upgrade groundedness from span-overlap to an **LLM-graded** check (does each answer claim follow from
  the retrieved chunks?), and write up where it disagreed with span-overlap and why that grader now
  needs its *own* eval.
- Sweep `CHUNK_SIZE` across several values, plot recall@3 against chunk size, and pick the operating
  point deliberately — the chunking dial, tuned by measurement instead of feel.
