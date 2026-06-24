# Lab 11 — Eval Harness for Security Tools

*Hands-on lab · [← Back to the module concept](README.md)*

> **Lab environment: real-data rewire — validation deferred.** The labelled corpus is now anchored
> in **real** loghub OpenSSH attack traffic (see below) rather than a wholly synthetic log. The env
> (`docker-compose.yml`, `Makefile`, `eval.py`, the corpus + answer key under `data/`) is in place;
> `make up && make demo && make down` has **not** yet been re-run on a clean Linux runner against
> this change — validate before marking the lab done.

## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/python-for-security/11-eval-harness
make up         # Python 3.12 container with pytest + coverage; no network, no model
make demo       # scores a GOOD parser (gate passes, exit 0), then a REGRESSED one
                # (under-detects attacks — gate fails, exit 1), and prints the verdict
make shell
make down
```

**Requirements:** Docker only. No GPU, no model, no network — the eval grades a deterministic Python
detection tool over a committed labelled corpus, so the whole lab is offline and reproducible (CI
included). Pure stdlib.

`data/auth-corpus.jsonl` is a labelled corpus of SSH-auth log lines whose **attack backbone is real**:
the fast brute force from `103.99.0.122` and the invalid-user dictionary sweep from `5.188.10.180` are
verbatim lines from [**loghub**](https://github.com/logpai/loghub)'s `OpenSSH_2k.log` — a real
internet-facing server's auth log — including the genuine `5.36.59.76` `message repeated 5 times:`
meta-line. Layered on top, on the same real `LabSZ` host format, are the deliberate **near-misses**
the real capture doesn't isolate cleanly (the `cron` job that mistypes its password twice a night; the
truncated/Unicode-mangled line; the slow-and-low spray that never trips a per-minute threshold). Every
line carries a `src` field marking it `loghub OpenSSH_2k.log` vs. `crafted ...`, and each source IP is
tagged `attack` or `benign` in `data/auth-labels.json` with a `reason` you can audit — **you own the
labels**. `scripts/parser_good.py` is a tuned version of the Module-02 brute-force flagger;
`scripts/parser_regressed.py` is the same tool with a weakened rule that silently under-detects the
slow-and-low case (recall regression).

## Scenario
Your Module-02 log parser flags SSH brute-force offenders, and Module 10's tests prove the code does
what you wrote. Your SOC lead asks the question the tests can't answer: *is it actually catching the
attacks, and how often is it crying wolf — and how will we know the day someone "improves" the regex
and quietly breaks it?* Your job is to stop trusting the demo log: build a held-out labelled corpus,
score the parser into a precision/recall scorecard, find the operating point deliberately, and wire a
CI gate that fails the build when detection quality regresses.

> Everything runs locally against committed fixtures. No external targets, no live systems, no
> authorization needed.

## Do

1. [ ] **Read the corpus, and understand *why* it's held out.** Open `data/auth-corpus.jsonl` and
   `data/auth-labels.json`. Confirm it is **separate from the Module-02 sample log** the parser was
   tuned against. Skim three `attack` lines and three `benign` lines and find at least two **near-miss
   pairs** you could not separate with a single keyword (e.g. the benign `cron` double-failure vs. a
   real two-attempt spray). That coverage of the *hard* cases — not just *more* lines — is the point.

2. [ ] **Run the parser over the corpus → recorded verdicts.** `make classify` runs
   `scripts/parser_good.py` over the corpus and writes its per-line verdicts to
   `results/verdicts-good.json`. Confirm you have a list of `attack`/`benign` calls to grade against
   the answer key — not a vibe.

3. [ ] **Build the scorecard — and pick the metric on purpose.** Write (or complete) `eval.py` so it
   compares the verdicts to the labels and prints the **confusion matrix** (TP/FP/FN/TN) plus
   **precision, recall, F1, FP-rate, and accuracy**. Read them off. Then write down, in one sentence in
   `eval-report.md`, **why recall is the load-bearing metric for this detector and why accuracy is
   dangerous here** — and prove it: note that a do-nothing parser scores ~85% accuracy on this
   imbalanced corpus while catching zero attacks.

4. [ ] **Watch the gate pass on good and FAIL on a regression — the core lesson.** `make demo` runs
   `eval.py --gate recall=0.85` on `verdicts-good.json` (passes, exit 0) and on the output of
   `scripts/parser_regressed.py` (a weakened rule that marks real attacks as benign — fails, exit 1).
   Open `parser_regressed.py` and confirm the regression is **under-detection** (false "all clear"),
   the failure that buries the alert that mattered. The green/red contrast is what lets a teammate
   refactor the parser without praying.

5. [ ] **Find the precision/recall knee.** Re-run the gate with a stricter floor:
   `make gate RECALL_MIN=0.95`. The good parser may now *fail* — "good" depends entirely on the bar you
   declared. Then loosen the parser's rule (broaden the regex) and re-score: watch recall rise and
   precision fall as the FP queue floods. Record the operating point you'd ship and justify it against
   the FP-rate cost in `eval-report.md`.

6. [ ] **Show coverage ≠ effectiveness.** Run `coverage run -m ... && coverage report` over the parser
   against an *easy* slice of the corpus and note the high line-coverage. Then point out in your report
   that the same coverage number says nothing about whether the hard near-misses are caught — coverage
   is a foil for detection quality, never a substitute.

## Success criteria — you're done when
- [ ] `make demo` runs offline and ends with `PASS: gate is GREEN on the good parser and RED on the regression`.
- [ ] `make eval` prints a scorecard (confusion matrix + precision/recall/F1/FP-rate/accuracy) for the parser over the held-out corpus.
- [ ] You can state, in writing, why **recall** is the metric — and why accuracy misleads on this imbalanced corpus (you've seen the do-nothing baseline score ~85% accuracy at 0% recall).
- [ ] You've moved the gate floor and the parser's rule and watched the precision/recall tradeoff move.
- [ ] `eval-report.md` is filled in: chosen metric + threshold + justification, the precision/recall knee, and the coverage-≠-effectiveness note.

## Deliverables
`eval.py` + the labelled corpus (`data/auth-corpus.jsonl`, `data/auth-labels.json`) + `eval-report.md`,
all committed. The eval-as-code **is** the artifact: a held-out corpus, a scorecard, and a gate that
fails on regression. Do **not** commit generated run outputs (`results/verdicts-*.json`, coverage
data) — they're gitignored; the corpus and the eval regenerate them.

## Automate & own it
**Required.** Wire the gate into CI so a detection regression *cannot merge*. Add a
`.github/workflows/eval.yml` (in your own portfolio repo) that runs, on every PR:
```
python3 eval.py --corpus data/auth-corpus.jsonl --labels data/auth-labels.json \
                --tool scripts/parser.py --gate recall=0.90
```
Have a model draft the workflow YAML — it's boilerplate. **You own three things it will get wrong:**
(1) the gate must **fail closed** — if `eval.py` errors or the metric is missing, the build fails, it
does not silently pass (verify by running the gate with a typo'd metric name and confirming a non-zero
exit); (2) the threshold and its *direction* (a recall *floor*, not a "score exists" check);
(3) that the corpus fed to CI is the *held-out* one, never the lines the parser was tuned on. Commit
the workflow and a log/screenshot of it going red on the planted regression.

## AI acceleration
Have a model **expand the corpus with adversarial near-misses** — benign lines crafted to look like
brute-force, and real attacks phrased to dodge the obvious regex — then **label every one yourself**
and verify it against what the line actually represents. A model labelling its own corpus is exactly
the contamination this module warns about; you generate candidates, you own the ground truth. Then ask
a frontier model to critique your metric choice ("I'm gating on recall@0.90 for an SSH brute-force
detector — what am I missing?") and weigh its answer against the FP-rate cost you measured.

## Connects forward
This is the measurement discipline behind every tool in the track. The Module-02 parser and the
Module-05 CLI tool get a scorecard instead of a demo; the Module-10 test suite gains an eval gate
alongside its unit tests. It's the deterministic-tool sibling of the AI-ops track's
[AI Evaluation & Observability](../../../12-ai-augmented-ops/modules/11-ai-evaluation/README.md) module,
which applies the same held-out-corpus / scorecard / regression-gate construct to a non-deterministic
model. The track capstone's tool should ship with one.

## Marketable proof
> "I don't just claim my detection tool works — I built it a held-out labelled corpus, a
> precision/recall scorecard chosen for the asymmetric cost of a missed alert, and a CI gate that
> fails the build the day a change drops recall. My tools have a number, not a vibe."

## Stretch
- Add a **precision/recall curve**: sweep the rule's threshold (e.g. attempts-per-window) over the
  corpus and print recall vs. FP-rate, then pick the operating point deliberately instead of by feel.
- Add a **malformed-input slice** to the corpus (truncated lines, bad encodings, injected newlines) and
  gate that the parser *neither crashes nor mis-classifies* on it — robustness as a measured property.
