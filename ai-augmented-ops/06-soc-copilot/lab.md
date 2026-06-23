# Lab 06 — A SoC Copilot, and the end-to-end scorecard that holds it accountable

*Hands-on lab · [← Back to the module concept](README.md)*

**Type 7 · Build-&-Operate (+ Type 13 · Eval Harness, end-to-end).** You finish the RAG + MCP + LLM
copilot with "show-its-work" auditability, then build the eval the type pass flagged as missing: an
**end-to-end scorecard** that grades the copilot on three axes — **tool-selection correctness**
(Module 07's confusion matrix), **retrieval relevance** (Module 04's recall@k), and **answer
groundedness** — over a *held-out* set of SOC questions, wired to a regression gate that plugs into
Module 11's harness. The flagship system gets a scorecard, not vibes.

## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/06-soc-copilot
make up && make demo
```

**Requirements:** Docker, 8 GB RAM free. No GPU needed. Three containers start: Ollama (generation),
ChromaDB (vector store), and the copilot app. First run downloads `tinyllama` (~637 MB) and
`nomic-embed-text` (~274 MB) and ingests the knowledge base. `make demo` asks the copilot
"Is 185.220.101.42 malicious?" and prints the full reasoning chain — retrieved chunks, tool calls,
and the generated answer — **and then runs the end-to-end eval over the held-out question set and
prints the scorecard**, so you see the build and its measurement in one pass.

This lab reuses the knowledge base from Module 04 and the alert/incident/threat-intel seed data behind
the Module 05 tools; both are bundled here, so you need not complete those modules first — but the lab
assumes you understand the recall@k metric from 04 and the confusion matrix from 07, because the
end-to-end eval is built from both.

> The tool-selection and retrieval halves of the eval score *recorded* copilot runs against a
> committed labelled set, so once a run is captured that scoring is deterministic and CI-friendly —
> the same offline discipline as Modules 04 and 11. Only the live answer-generation step needs Ollama.

## Scenario
A security team is testing its new copilot before going live. The copilot answers questions by
combining institutional knowledge (past incidents, runbooks) with live data (current alerts, threat
intel, open incidents). Your job is twofold: finish the copilot so its reasoning is fully auditable,
and then **prove it works the way a flagship system must be proven** — not with a demo it passes, but
with a held-out scorecard that decomposes its failures by layer. A copilot that confidently tells an
analyst "no open incident on that host" because it never called the right tool is worse than no
copilot; the end-to-end eval is how you catch that before 3 a.m.

> Test prompt-injection and adversarial techniques only against models and applications you own or are
> explicitly authorised to assess. This lab runs entirely locally against bundled seed data — no cloud
> API keys, no external targets, no authorization needed.

## Do

### Part A — Operate the copilot and read its reasoning chain

1. [ ] `make demo` and read the full output. The demo asks "Is 185.220.101.42 malicious?" — identify
   in the trace:
   - the **retrieved chunks** (which knowledge-base documents did RAG return?),
   - the **tool call(s)** the router fired (which tool, which argument?),
   - whether the generated answer *accurately reflects* the tool result and the retrieved context,
   - any claim in the answer **not supported** by the evidence shown (hallucination-on-context).
   Write one sentence: judged by the prose alone, could you tell whether the *retrieval* or the *tool
   routing* had failed? (This is why the eval decomposes by layer.)

2. [ ] Run four more questions and watch the three layers each behave:
   ```bash
   make ask Q="What containment steps should I follow for a ransomware event?"
   make ask Q="Is there an open incident for host WKS-023?"
   make ask Q="What is the SLA for patching a Critical CVSS vulnerability?"
   make ask Q="Summarise the credential phishing incident from 2024."
   ```
   For each, note: was retrieval relevant, did the router call the *right* tool (or miss one / fire a
   spurious one), and did the answer stay grounded? The host question is the canonical tool-routing
   test — does it call `search_alerts`/`summarize_incident`, or answer from RAG priors alone?

3. [ ] **Make the work auditable.** Open `copilot/copilot.py` (`make shell`). Confirm the output
   shows which facts came from RAG (`[RAG: filename]`), which from tool calls (`[TOOL: name]`), and
   which from the model. If provenance is unclear, strengthen the system prompt to require every
   factual claim to carry its source tag, and re-run a question to confirm. Auditability is the
   precondition for the eval — you can only score tool-selection and groundedness if the trace records
   them.

### Part B — Build the end-to-end eval (the deliverable)

4. [ ] **Read the held-out question set and its three-axis answer key.** `data/eval-questions.json`
   holds ~15 realistic SOC questions, each labelled with: the **expected tools** (which of
   `get_threat_intel` / `search_alerts` / `summarize_incident` *should* fire, and with what kind of
   argument), the **relevant knowledge-base doc(s)** (the recall@k key, reused from Module 04's
   labelling discipline), and a short **answer rubric** (the facts a grounded answer must contain).
   These questions are **held out** — separate from the demo question and never used to tune the tool
   heuristics or the prompt. Skim three and confirm each label is a *judgment about the data*: the
   "open incident on a host" question should expect a `search_alerts`/`summarize_incident` call even
   though the question never names a tool — that's tool-selection correctness, not keyword matching.

5. [ ] **Score tool-selection correctness (Module 07's confusion matrix).** `make eval` runs each
   held-out question through `decide_tools`, compares the tools fired against the expected set, and
   writes a **per-tool confusion matrix** to `results/copilot-scorecard.md`: per-tool
   precision/recall plus the misses. Read it as numbers. Which tool is *under-called* (a recall hole —
   the costly error, per Module 07's asymmetry: a missed `summarize_incident` buries the open
   incident) and which is *over-called* (a precision hole — wasted lookups)? Note one routing rule in
   `decide_tools` you'd change and why.

6. [ ] **Score retrieval relevance (Module 04's recall@k, reused).** `make eval` also embeds each
   held-out question, retrieves the top-k chunks the copilot would, and reports **recall@1 / @3 / @5**
   against the labelled relevant doc(s) — the *same metric* you built in Module 04, over the *same*
   corpus. Which questions miss at k=3, and is it a phrasing, chunk-boundary, or vocabulary gap?
   Confirm for yourself that this is the literal recall@k from 04 plugged in, not a new metric.

7. [ ] **Score answer groundedness.** `make eval` runs the live copilot on each held-out question and
   computes a minimal **groundedness** score — span overlap between the answer's claims and the
   evidence it was actually given (**both** retrieved chunks and tool results). Find the question whose
   answer read most confidently but scored *worst* on groundedness — that gap is the silent failure
   the module is about, and note where span-overlap is too crude (and why an LLM-grader would
   re-introduce the eval-the-evaluator problem from Module 11).

8. [ ] **Prove the regression gate catches a real degradation.** `make gate` runs the full eval
   against declared floors (e.g. `tool_recall=0.80`, `retrieval_recall_at_k=0.80`,
   `groundedness=0.60`) and exits non-zero if *any* axis drops below its floor. Now *cause* a
   regression on one axis: break tool routing by commenting out the incident/alert branch in
   `decide_tools` (so host questions never call a tool), re-run `make gate`, and watch tool-recall
   collapse and the gate go **red (exit 1)** — while retrieval stays green, proving the scorecard
   *localises* the failure. Restore the branch, re-run, confirm **green (exit 0)**. The
   green-on-good / red-on-one-axis contrast is the whole point: a "harmless" routing edit silently
   blinds the copilot, and the gate is what stops it merging.

9. [ ] **Extend the held-out set with a hard, cross-layer case.** Add one question whose correct
   answer needs **both** a retrieval hit *and* a tool call (e.g. "What's our runbook for an alert on
   WKS-023, and is there an open incident on it?"). Label all three axes, re-run `make eval`,
   and see whether the copilot scores well on a question that exercises every layer at once — the case
   that "more single-layer questions" would never catch (coverage ≠ effectiveness).

## Success criteria — you're done when
- [ ] `make demo` runs to completion: the reasoning chain (chunks + tool calls + answer) *and* the
      end-to-end scorecard print in one pass.
- [ ] `make eval` produces `results/copilot-scorecard.md` with all three axes: per-tool
      precision/recall (confusion matrix), recall@1/@3/@5, and a groundedness number — plus per-item
      misses.
- [ ] You can state, in writing, **why a copilot needs a *three-axis* scorecard and not a single
      "answer reads well" check** — and you've seen one confident answer score low on groundedness and
      one tool routinely under-called.
- [ ] `make gate` exits **0** on the good copilot and **1** after you break the tool-routing branch —
      and you watched tool-recall collapse while retrieval stayed green (the failure was *localised*).
- [ ] Your added cross-layer question is labelled on all three axes, committed, and scored.

## Deliverables
`data/eval-questions.json` (the held-out, three-axis labelled set, including your added cross-layer
question) + `scripts/eval.py` (the end-to-end scorer + gate, with any metric/threshold change you
made) + `copilot/copilot.py` (with your auditability/routing improvement) +
`results/copilot-scorecard.md`, all committed. **The end-to-end scorecard is the headline artifact**:
a held-out question set graded on tool-selection correctness, retrieval relevance, and groundedness,
with a gate that fails on a regression in *any* axis. Do **not** commit live run dumps
(`results/predictions-*.json`, raw chunk/answer text) — they're gitignored and regenerate from the
corpus + eval. The copilot is the attack target for Module 09, and this scorecard becomes the
regression test that proves a Module 09 mitigation holds.

## Automate & own it
**Required.** Wire the end-to-end gate into CI so a regression in *any* axis cannot merge. Add a
`.github/workflows/copilot-eval.yml` (in your own portfolio repo) that, on every PR, brings up the
stack, captures a copilot run over the held-out set, and runs:
```
python3 scripts/eval.py --questions data/eval-questions.json \
    --gate tool_recall=0.80 --gate retrieval_recall_at_k=0.80 --gate groundedness=0.60
```
Have a model draft the workflow YAML — it's boilerplate. **You own three things it will get wrong:**
(1) the gate must **fail closed** — if the stack fails to come up, a copilot run errors, or *any* of
the three axes is missing, the build fails; it does not silently pass (verify by deleting one axis's
floor or feeding a typo'd metric name and confirming a non-zero exit); (2) each floor is a *real
metric floor* per axis, not a "did it produce output" check, and the tool axis is weighted toward
**recall** (a missed tool call is the costly error); (3) the questions fed to CI are the **held-out**
labelled set, never the demo question. Commit the workflow and a log of it going red on the broken
`decide_tools` branch.

## AI acceleration
Have a model **draft candidate held-out questions** — including hard ones that need both a retrieval
hit and a tool call — then **label all three axes yourself**: open the source docs to confirm the
relevant chunk, and decide which tools *should* fire by reasoning about the question, not by running
the copilot and recording what it happened to do (that would grade the system against its own
behaviour — the contamination Module 11 warns about). For groundedness spot-checks, paste a
low-scoring answer plus the exact chunks and tool results it was given into a frontier model and ask
"which claims here are *not* supported by this evidence?" — then verify its verdict against the
evidence yourself, because trusting the grader uncritically is the same mistake one level up.

## Connects forward
This copilot is the attack target for **Module 09 (Securing the AI You Run)** — prompt injection via
alert text, context poisoning via a malicious knowledge-base document, and tool-result manipulation
are all demonstrated against this stack, and the end-to-end scorecard you built here becomes the
**regression test** that proves each mitigation holds without quietly tanking another axis. **Module
11** is where this harness is generalised — the same held-out + scorecard + gate discipline across
triage, RAG, and the copilot together; this module is its hardest instance, the one that scores three
layers at once. **Module 04**'s retrieval eval and **Module 07**'s confusion matrix are the two halves
you reused to build it.

## Marketable proof
> "I built a SoC copilot that fuses RAG over a private corpus with live MCP tool calls and full
> evidence traceability — *and* I built its end-to-end eval: a held-out SOC-question set scored on
> tool-selection correctness (a per-tool confusion matrix), retrieval relevance (recall@k), and answer
> groundedness, with a CI gate that fails on a regression in any one axis. I measure the flagship
> system the most, not the least."

## Stretch
- Upgrade groundedness from span-overlap to an **LLM-graded** faithfulness check over the combined
  RAG + tool evidence, and write up where it disagreed with span-overlap and why that grader now needs
  its *own* eval.
- Add a **tool-argument correctness** sub-score: it's not enough that `get_threat_intel` fired — did
  it fire on the *right* IOC? Extend the tool axis to grade the argument, not just the tool name.
- Add a **confidence-vs-correctness** plot: have the copilot self-rate confidence (1–5) per answer,
  then chart confidence against the eval's groundedness score — the calibration gap (confident *and*
  ungrounded) is the answer class that most deserves a human's eyes.
