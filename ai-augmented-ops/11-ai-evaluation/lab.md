# Lab 11 — Eval Gates, Not Vibes: catch a silent regression before it ships

> **Hands-on lab.** Environment: `plaintext-labs/ai-augmented-ops/11-ai-evaluation`.
> Objective: **prove an AI security system is good with a number, not an adjective** — build a
> held-out scorecard and a CI regression gate, then watch it go **green on a good system and red on a
> planted regression**. Target: **~90 min**, one finish line. Runs **offline, deterministic, no model,
> no GPU, no network** — the eval grades *recorded* system outputs (committed fixtures), pure Python
> stdlib. That determinism is the point: a gate you can trust in CI cannot depend on a live model's mood.

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **A demo is a memorised exam.** | The inputs you watched it ace are the ones you tuned on — "it got the demo right" is no evidence. |
| 2 | **The held-out wall.** Tune on one set, grade on another. | Score on the tuning set and every number is inflated by the memorisation that makes the demo lie. |
| 3 | **Metric choice is a judgment:** recall on the malicious class + FN-rate, **not** accuracy. | Imbalanced classes, asymmetric cost: a 95%-*accurate* model that ignores the rare attack is worthless. |
| 4 | **Coverage ≠ effectiveness.** | 500 easy items beat none but lose to 30 near-misses — test the cases that *break* it, not just more. |
| 5 | **The regression gate.** A planted regression must turn the build **red** and exit non-zero. | A gate you've only ever seen pass isn't a gate — you never showed it can catch anything. |
| 6 | **Fail closed.** Missing metric / errored eval → build fails, never silently "passes." | A gate that greens on a broken eval is worse than none: it launders a silent regression. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea) (held-out wall, metric choice, the gate) and the
> [case-study seam](README.md#the-core-idea) — silent regression is *Moffatt* one layer down.

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. Why does the demo set "actively lie" to you — and name the one **wall** that makes a score honest.
2. Which single number is the **load-bearing metric** for SOC triage, and why is *accuracy* dangerous
   on this data?

---

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/11-ai-evaluation
make up && make demo
```

**Requirements:** Docker, ~256 MB RAM. **No GPU, no model, no network.** `make demo` scores a **good**
triage system (gate passes, exit 0), then a **regressed** one that under-classifies attacks (gate fails,
exit 1), then the same for a RAG retriever — and prints a verdict confirming green-on-good / red-on-regression.
That contrast is the whole lesson.

> **▸ On track if:** `make demo` ends with
> `PASS: gate is GREEN on the good system and RED on the regression — the gate works.` and exits `0`.
> (Run `echo $?` to confirm.) If it prints `UNEXPECTED`, the gate is not discriminating — that is a
> broken gate, and finding that out here is exactly what the lab is for.

> **Authorization note.** Everything runs locally against committed fixtures — no live model, no external
> targets, no authorization needed. (Later modules *attack* AI systems; there the rule binds: only test
> systems you own or have written permission to test.)

---

## Build it — read a little, do a little

### Step 1 — Read the held-out corpus, and understand *why* it's held out

**Concept (30 sec):** Flight-card #1–2. `data/triage-heldout.jsonl` is 32 realistic alerts (16 malicious,
16 benign); the answer key is `data/triage-labels.json`. It is **separate from the Module-07 demo/tuning
set** — alerts the triage prompt was never tuned against, seeded with deliberate **near-misses** (the
benign `certbot` renewal vs. the malicious hidden `DownloadString`; the benign backup VSS job vs. the
malicious `vssadmin Delete Shadows`).

**Do it:** skim three malicious and three benign items. Find a near-miss pair you could **not** separate
with a single keyword.

> **▸ On track if:** you can name one benign/malicious pair that shares surface features — proof the set
> tests the hard cases (coverage of what *breaks* the system, Flight-card #4), not just *more* cases.

### Step 2 — Run the system over the held-out set → recorded predictions

**Concept (30 sec):** In real use you drop in your Module-07 model; here a deterministic **stub** stands
in so the loop runs offline. The corpus, eval, and gate are identical either way.

**Do it:** `make classify` — runs `scripts/stub_classifier.py` over the corpus, writes
`results/predictions-stub.json`, then scores it.

> **▸ On track if:** you get a **scorecard** — a confusion matrix plus precision / recall / F1 printed to
> the terminal — not a vibe. (`results/` is gitignored; the corpus + eval regenerate it.)

### Step 3 — Read the metric off the scorecard and decide if it's the right one

**Concept (30 sec):** Flight-card #3. A scorecard is only as honest as its metric, and accuracy is
usually the wrong one.

**Do it:** `make eval` prints precision, recall, F1, **FN-rate**, FP-rate **and** accuracy on
`data/predictions-good.json`. Find the line marked *the metric that matters* and write, in one sentence,
**why recall on the malicious class (and its FN-rate) is load-bearing for SOC triage, and why accuracy
alone is dangerous here.**

> **▸ On track if:** the scorecard prints all six numbers and you can point to **recall on the malicious
> class** as the one you'd gate on — and say why a missed critical costs a breach while a false positive
> costs an analyst minutes.

### Step 4 — Watch the gate pass on good and FAIL on a regression *(the core lesson)*

**Concept (30 sec):** Flight-card #5. The proof a gate works is a **planted regression** that must turn
it red.

**Do it:** `make demo` runs the gate at `recall=$(TRIAGE_RECALL_MIN)` (0.80) on `predictions-good.json`
(passes, exit 0) and on `predictions-regressed.json` (a model that started marking real attacks as
"benign" — fails, exit 1). Open `data/predictions-regressed.json` and confirm the regression is
*under-classified maliciousness* (false "all clear") — the failure that buries the alert that mattered
under a green dashboard.

> **▸ On track if:** the two runs report **different exit statuses** — good exits `0`, regressed exits
> non-zero — and the run notes accuracy stays ~69% while recall collapses to ~37.5% on the regression.
> Same accuracy, wildly different recall: that is *why* you don't gate on accuracy.

### Step 5 — Tune the threshold and watch the tradeoff move

**Concept (30 sec):** "Good" is not absolute — it's relative to the bar you *declare*.

**Do it:** re-run the gate with a stricter floor: `make gate TRIAGE_RECALL_MIN=0.95`. The good system
(recall 0.938) now **fails**.

> **▸ On track if:** the *same* good predictions that passed at 0.80 now exit non-zero at 0.95 — you've
> discovered "good" depends entirely on the declared floor. Pick a defensible SOC floor and justify it
> against the FP-rate cost in `eval-report.md` (push recall up → the analyst queue floods; the eval finds
> the knee deliberately).

### Step 6 — Do the same for RAG retrieval

**Concept (30 sec):** A RAG needs a *retrieval* metric, not a "the answer read well" check — confident
generation on top of wrong context is the silent failure.

**Do it:** `make eval-rag` scores `data/retrieval-good.json` against `data/rag-heldout.json` with
**retrieval@k** (did a genuinely-relevant doc land in the top-k?). Then look at
`data/retrieval-regressed.json` — a retriever that pulls generically-similar but wrong chunks.

> **▸ On track if:** `retrieval@3` drops sharply from the good retriever (~92%) to the regressed one
> (~42%), and the regressed run exits non-zero against the `recall_at_k=$(RAG_RECALL_MIN)` floor.

---

## Prove the control — your finish line

One command, one deterministic verdict — the **pass/fail pair** that *is* the deliverable's proof:

```bash
make demo          # good → gate GREEN (exit 0);  regression → gate RED (exit 1)
echo $?            # 0 only if green-on-good AND red-on-regression
```

You're done when `make demo` prints
`PASS: gate is GREEN on the good system and RED on the regression — the gate works.` and exits `0`.
The good predictions clear the recall floor; the deliberately-regressed ones (real attacks marked
"benign") do not. **A gate you have only ever seen pass is not a gate** — the red half is the whole
point. Then add the standing version: in `eval-report.md`, write the one-paragraph **observability**
plan — what you'd log in production (inputs, outputs, scores, realised outcomes) and how re-scoring last
month's labelled traffic catches **input-distribution drift** before an analyst does.

---

## Recall check — close the doc, answer from memory (3 min)

1. Why does the demo set "actively lie," and what is the one **wall** that makes a score honest?
2. Why is accuracy the wrong metric for SOC triage, and which metric replaces it — and why?
3. What is a **planted regression**, and why isn't a gate you've only ever seen pass actually a gate?

---

## Deliverables

`scripts/eval.py` (with any metric or gate change you made) + the **held-out corpus** + `eval-report.md`,
all committed. The eval-as-code **is** the artifact: a held-out set, a scorecard, and a gate that fails
on regression. Do **not** commit generated run outputs (`results/predictions-stub.json`, metric dumps) —
they're gitignored; the corpus and the eval regenerate them.

## Automate & own it

**Required — the eval gate *is* the automation.** Wire it into CI so a regression *cannot merge*. Add a
`.github/workflows/eval.yml` (in your own portfolio repo) that runs, on every PR:

```
python3 scripts/eval.py triage --predictions <your model's output> --gate recall=0.85
python3 scripts/eval.py rag    --retrieval   <your retriever's output> --gate recall_at_k=0.75
```

Have a model draft the workflow YAML — it's boilerplate. **You own three things it will get wrong:**
(1) the gate must **fail closed** — if the eval errors or the metric is missing, the build fails, it does
not silently pass (verify by running the gate with a typo'd metric name and confirming a non-zero exit);
(2) the threshold and its *direction* (a recall floor, not a "score exists" check); (3) that the
predictions fed to CI come from a *held-out* set, never the tuning set. Commit the workflow and a
screenshot/log of it going **red** on a planted regression.

## Definition of done (`ai-evaluation` ✅)

- [ ] `make demo` runs offline and ends with `PASS: gate is GREEN on the good system and RED on the regression` (exit 0).
- [ ] `make eval` prints a triage scorecard (confusion matrix + precision/recall/F1/FN-rate/FP-rate).
- [ ] You can state, in writing, why **recall/FN-rate on the malicious class** is the metric — and why accuracy misleads here (you've seen the regressed run prove it: ~69% accuracy, ~37.5% recall).
- [ ] `make eval-rag` prints retrieval@k, and you've seen the gate fail on the regressed retriever.
- [ ] `eval-report.md` is filled in: chosen metric + threshold + justification, the FP/recall tradeoff, and the observability plan.
- [ ] The CI `eval.yml` fails closed on a typo'd metric name (proven, not assumed).

## Connects forward

This is the measurement layer the rest of the track plugs into. **Module 04 (RAG)** gets the retrieval@k
gate; **Module 06 (SoC copilot)** gets a groundedness check on its summaries; **Module 07 (triage)** swaps
its one-off confusion matrix for this held-out scorecard + gate. **Modules 09/10 (securing/attacking AI)**
reuse the gate as a *regression test for a fixed jailbreak*: the exploit must stay blocked, proven by an
eval that fails if it ever works again.

## Marketable proof

> "I built an eval harness for an AI security system — a held-out labelled corpus, a recall/FN-rate
> scorecard chosen for the asymmetric cost of a missed alert, and a CI regression gate that fails the
> build on a planted degradation. I can prove my model is good, not just claim it."

## Stretch

- Add a **precision/recall curve**: sweep a confidence threshold over a graded-confidence prediction
  fixture and plot (or print) recall vs. FP-rate, then pick the operating point deliberately.
- Add a **groundedness** check to the RAG eval: given retrieved chunks and a generated answer, score
  whether the answer's claims are supported by the retrieved text (start with simple span overlap; note
  where it needs an LLM-grader and why that re-introduces the eval-the-evaluator problem).
