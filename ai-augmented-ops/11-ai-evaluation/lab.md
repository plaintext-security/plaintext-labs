# Lab 11 — AI Evaluation & Observability

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/11-ai-evaluation
make up && make demo
```

**Requirements:** Docker. ~256 MB RAM. **No GPU, no model, no network** — the eval grades
*recorded* system outputs (committed fixtures), so the whole lab is deterministic and runs offline,
in CI too. Pure Python stdlib.

`make demo` scores a **good** triage system (the gate passes), then a **regressed** one that
under-classifies attacks (the gate fails), then does the same for a RAG retriever — and prints a
verdict confirming the gate is green on good and red on the regression. That contrast is the whole
lesson.

## Scenario
You built a triage classifier in Module 07 and a RAG in Module 04. Both looked good in the demo.
Now a model upgrade is queued for Friday and your lead asks the question you cannot answer with
adjectives: *is it still good enough to route real alerts and answer real questions — and how will
we know the day it stops being?* Your job is to stop trusting the vibe: build a **held-out** test
set, choose a **metric** and defend it, score the system into a **scorecard**, and wire a **CI
regression gate** that fails the build when quality drops.

> Everything runs locally against committed fixtures. No external targets, no live model, no
> authorization needed.

## Do

1. [ ] **Read the held-out corpus, and understand *why* it's held out.**
   `data/triage-heldout.jsonl` is 32 realistic alerts (16 malicious, 16 benign), with the answer
   key in `data/triage-labels.json`. Note it is **separate from the Module-07 demo/tuning set** — it
   contains alerts the triage prompt was never tuned against, including deliberate **near-misses**
   (the benign `certbot` renewal vs. the malicious hidden `DownloadString`; the benign backup VSS
   job vs. the malicious `vssadmin Delete Shadows`). Skim three malicious and three benign items and
   confirm you could not separate them with a single keyword — that's the point: coverage of the
   hard cases, not just *more* cases.

2. [ ] **Run the system over the held-out set → recorded predictions.**
   `make classify` runs the deterministic **stub classifier** (`scripts/stub_classifier.py`) over
   the corpus and writes `results/predictions-stub.json`, then scores it. The stub is an honest
   stand-in so the loop runs offline — in real use you delete it and drop in your Module-07 model;
   the corpus, eval, and gate are unchanged. Confirm you get a scorecard, not a vibe.

3. [ ] **Read the metric off the scorecard and decide if it's the right one.**
   `make eval` prints precision, recall, F1, **FN-rate**, FP-rate, **and** accuracy on the
   `predictions-good.json` fixture. Find the line marked *the metric that matters* and write down,
   in one sentence, **why recall on the malicious class (and its FN-rate) is the load-bearing number
   for SOC triage, and why accuracy alone is dangerous here.** Then prove it to yourself: run the
   gate on the regressed system below and watch accuracy stay ~69% while recall collapses.

4. [ ] **Watch the gate pass on good and FAIL on a regression — the core lesson.**
   `make demo` runs `eval.py ... --gate recall=0.80` on `predictions-good.json` (passes, exit 0)
   and on `predictions-regressed.json` (a model that started marking real attacks as "benign" —
   fails, exit 1). Open `data/predictions-regressed.json`; confirm the regression is *under-classified
   maliciousness* (false "all clear"), the failure that buries the alert that mattered. The green/red
   contrast is what lets a team upgrade a model without praying.

5. [ ] **Tune a threshold and watch the tradeoff move.**
   Re-run the gate with a stricter floor: `make gate TRIAGE_RECALL_MIN=0.95`. The good system
   (recall 0.938) now *fails* — you've discovered that "good" depends entirely on the bar you
   declared. Pick a defensible floor for a SOC and justify it against the FP-rate cost in your
   `eval-report.md` (push recall up and you flood the analyst queue; the eval is how you find the
   knee deliberately).

6. [ ] **Do the same for RAG retrieval.**
   `make eval-rag` scores `retrieval-good.json` against `data/rag-heldout.json` with **retrieval@k**
   (did a genuinely-relevant doc land in the top-k?). Then look at `retrieval-regressed.json` — a
   retriever that pulls generically-similar but wrong chunks — and confirm `retrieval@3` collapses
   from ~92% to ~42%. Note in your report why a RAG needs a *retrieval* metric and not just a
   "the answer read well" check: confident generation on top of wrong context is the silent failure.

7. [ ] **Add observability.** In `eval-report.md`, write the one-paragraph plan for the *standing*
   version of this eval in production: what you would log (inputs, outputs, scores, realised
   outcomes) and how re-scoring last month's labelled traffic catches **input-distribution drift**
   before an analyst does.

## Success criteria — you're done when
- [ ] `make demo` runs offline and ends with `PASS: gate is GREEN on the good system and RED on the regression`.
- [ ] `make eval` prints a triage scorecard (confusion matrix + precision/recall/F1/FN-rate/FP-rate).
- [ ] You can state, in writing, why **recall/FN-rate on the malicious class** is the metric — and why accuracy misleads on this imbalanced set (you've seen the regressed run prove it: ~69% accuracy, 37.5% recall).
- [ ] `make eval-rag` prints retrieval@k, and you've seen the gate fail on the regressed retriever.
- [ ] `eval-report.md` is filled in: chosen metric + threshold + justification, the FP/recall tradeoff, and the observability plan.

## Deliverables
`eval.py` (with any metric or gate change you made) + the held-out corpus + `eval-report.md`, all
committed. The eval-as-code **is** the artifact: a held-out set, a scorecard, and a gate that fails
on regression. Do **not** commit generated run outputs (`results/predictions-stub.json`, metric
dumps) — they're gitignored; the corpus and the eval regenerate them.

## Automate & own it
**Required.** Wire the gate into CI so a regression *cannot merge*. Add a `.github/workflows/eval.yml`
(in your own portfolio repo) that runs, on every PR:
```
python3 scripts/eval.py triage --predictions <your model's output> --gate recall=0.85
python3 scripts/eval.py rag    --retrieval   <your retriever's output> --gate recall_at_k=0.75
```
Have a model draft the workflow YAML — it's boilerplate. **You own three things it will get wrong:**
(1) the gate must **fail closed** — if the eval errors or the metric is missing, the build fails, it
does not silently pass (verify by running the gate with a typo'd metric name and confirming a
non-zero exit); (2) the threshold and its *direction* (a recall floor, not a "score exists" check);
(3) that the predictions fed to CI come from a *held-out* set, never the tuning set. Commit the
workflow and a screenshot/log of it going red on a planted regression.

## AI acceleration
Have a model **expand the held-out corpus with adversarial items** — benign events crafted to look
malicious, and novel techniques phrased unusually — then **label them yourself** and verify each
against the technique it mimics. A model labelling its own test set is exactly the contamination this
module warns about; you generate candidates, you own the ground truth. Ask a frontier model to
critique your metric choice ("I'm gating on recall@0.85 for SOC triage — what am I missing?") and
weigh its answer against the FP-rate cost you measured.

## Connects forward
This is the measurement layer the rest of the track plugs into. **Module 04 (RAG)** gets the
retrieval@k gate; **Module 06 (SoC copilot)** gets a groundedness check on its summaries; **Module 07
(triage)** swaps its one-off confusion matrix for this held-out scorecard + gate. **Modules 09/10
(securing/attacking AI)** reuse the gate as a *regression test for a fixed jailbreak*: the exploit
must stay blocked, proven by an eval that fails if it ever works again.

## Marketable proof
> "I built an eval harness for an AI security system — a held-out labelled corpus, a recall/FN-rate
> scorecard chosen for the asymmetric cost of a missed alert, and a CI regression gate that fails the
> build on a planted degradation. I can prove my model is good, not just claim it."

## Stretch
- Add a **precision/recall curve**: sweep a confidence threshold over a graded-confidence prediction
  fixture and plot (or print) recall vs. FP-rate, then pick the operating point deliberately.
- Add a **groundedness** check to the RAG eval: given retrieved chunks and a generated answer, score
  whether the answer's claims are supported by the retrieved text (start with simple span overlap;
  note where it needs an LLM-grader and why that re-introduces the eval-the-evaluator problem).
