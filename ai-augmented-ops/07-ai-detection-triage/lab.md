# Lab 07 — Trust It As Far As You Measured It: an AI triage eval

> **Hands-on lab.** Environment: `plaintext-labs/ai-augmented-ops/07-ai-detection-triage`.
> Objective: **build the eval for a local-model alert triage classifier** — score it on a *held-out*
> label set, read the confusion matrix, and prove **recall on the critical class** holds at a
> threshold you declare. Target: **~90 min**, one finish line. Runs entirely on **local
> infrastructure you own** (Ollama + `tinyllama`, CPU-only). Deliverable: the tuned classifier + a
> scored `accuracy-report.md`.

---

## ✈ Flight card — the 7 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **The model handles the familiar 80%; the analyst owns the escalated 20%.** | Triage is a *filter*, not a replacement — you trust it only as far as you have measured it. |
| 2 | **Score on the HELD-OUT set, never the demo/tuning set.** | The 5 demo alerts are a memorised exam; the honest number is the 50 the prompt never saw. |
| 3 | **Recall on CRITICAL/HIGH (+ false-negative rate) is the load-bearing metric — not accuracy.** | Accuracy looks great while the rare, costly miss is exactly what it hides. |
| 4 | **Bias the prompt toward over-classification** (uncertain → HIGH). | A false alarm costs an analyst minutes; a missed critical can cost a breach. |
| 5 | **Parse-or-flag, never silently drop.** | A malformed model response → flagged for human review, never garbage propagated to the queue. |
| 6 | **Automation bias = OWASP LLM09.** | A confidently-wrong "MEDIUM — likely benign" de-prioritizes a real alert; the recall number makes it visible. |
| 7 | **The monthly re-eval is the regression gate.** | A recall drop below the declared bar must fail loudly — caught by a number, not by a breach. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea) (the eval-harness shape) and the
> [overreliance trap](README.md#the-core-idea) (automation bias / LLM09).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. The model classifies all **5 demo alerts** correctly. Name the one reason that is **not** evidence
   it is ready to route real alerts.
2. A single **accuracy** number can look excellent on this corpus while the pipeline is dangerous.
   Which failure does it hide — and which metric replaces it?

---

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/07-ai-detection-triage
make up && make demo
```

**Requirements:** Docker, ~4 GB RAM free, no GPU. First `make up` pulls the Ollama image and
`tinyllama` (~637 MB); later runs use the cache. Seed files: **`data/alerts.jsonl`** (50 alerts,
fields `id · timestamp · host · title · description`) and **`data/ground-truth.json`** (the held-out
answer key: `severity · technique · rationale`).

**The make targets you'll use:** `make demo` (5 sample alerts + ground-truth compare), `make triage`
(the full 50-alert held-out batch → `results/triage-results.json`), `make eval` (confusion matrix +
per-class precision/recall/F1 → `results/accuracy-metrics.json`).

> **▸ On track if:** `make demo` prints 5 lines, each with a `severity` value and a `technique` ID,
> then a ground-truth comparison table ending in an `Accuracy: N/5` line. (Ollama is reachable and the
> model pulled.)

> **Authorization note.** Everything runs against local infrastructure you own — no external targets,
> no live SIEM or vulnerable Log4j2 instance. The 50 alerts are **synthetic but realistically shaped**
> from the [CVE-2021-44228 (Log4Shell)](https://nvd.nist.gov/vuln/detail/cve-2021-44228) exploitation
> wave — real JNDI strings, real ATT&CK techniques, human-analyst labels. You are evaluating a
> *classifier's* judgment against a *human's*, not reproducing the CVE.

---

## Build it — read a little, do a little

### Step 1 — Watch the memorised exam (the demo is the tuning set)

**Concept (30 sec):** Flight-card #2. The demo alerts are the ones the prompt was tuned on. A model
acing them tells you nothing about the alerts it hasn't seen — that's the train/dev/test wall.

**Do it:** `make demo`. For each of the 5, note predicted vs. true severity, whether it got the ATT&CK
technique ID, and whether it parsed cleanly as JSON or fell back to a `parse_error`.

> **▸ On track if:** you can point at the demo `Accuracy: N/5` line and say why a high number here is
> *not yet* evidence — because these five are the tuning set, not a held-out one.

### Step 2 — Run the held-out batch (the honest score starts here)

**Concept (30 sec):** Flight-card #2. The 50 alerts in `data/alerts.jsonl` are the held-out set — the
prompt was never tuned on them, so this is the number that means something.

**Do it:** `make triage`. It writes `results/triage-results.json` and prints a severity distribution.
Open the file: each entry carries `id · status · severity · confidence · technique · action ·
rationale`. Scan for any entry with `"status": "parse_error"`.

> **▸ On track if:** `results/triage-results.json` holds **50 entries**, each with a `severity` field,
> and you can tell how many (if any) came back `parse_error` and defaulted to a conservative `HIGH`.

### Step 3 — Score it into the confusion matrix

**Concept (30 sec):** Flight-card #3. Accuracy is a single number that hides the rare costly miss.
The confusion matrix (rows = true, cols = predicted) lets you *see* where CRITICAL/HIGH leak downward.

**Do it:** `make eval`. Read the per-class **recall on CRITICAL and HIGH** and the printed
**false-negatives-on-CRITICAL/HIGH** list. Record these in `results/accuracy-report.md` — and call out
the recall + false-negative rate as load-bearing, *not* the headline accuracy.

> **▸ On track if:** `make eval` prints a per-class precision/recall/F1 table, and you have written the
> **recall on the CRITICAL/HIGH classes** and the count of false negatives into your report — not just
> the overall accuracy percentage.

### Step 4 — Tune the prompt, then re-score against the same held-out set

**Concept (30 sec):** Flight-card #4. Biasing toward over-classification (uncertain → HIGH) is the
right call for security triage — you trade some false positives to buy back recall on the critical
class. The confusion matrix is where you pick that knee deliberately.

**Do it:** edit the `SYSTEM_PROMPT` in `scripts/triage.py` — add at least one concrete few-shot
example per severity level, and make the over-classification bias explicit. Re-run `make triage` then
`make eval`. Record before/after.

> **▸ On track if:** after your change, the **recall on CRITICAL/HIGH moved measurably** versus your
> Step-3 number (up, ideally), and you recorded both the recall and the false-positive cost of the
> move — the knee you tuned, not a vibe.

### Step 5 — Name one false call (the automation-bias moment)

**Concept (30 sec):** Flight-card #6. A confidently-worded under-classification is the OWASP LLM09
trap: it de-prioritizes a real alert, and a queue that's usually right invites the analyst to defer.

**Do it:** pick one **false negative** (ground-truth HIGH/CRITICAL the model scored lower) from the
held-out batch. Write a paragraph in `results/accuracy-report.md`: what in the alert *text* caused the
under-classification, what prompt change would help, and the FP-economics — what this one miss costs
versus the false alarms you'd accept to catch it.

> **▸ On track if:** your report names one alert `id` where true severity was CRITICAL/HIGH but the
> model predicted lower, with a text-level cause — not "the model was wrong."

---

## Prove the control (your finish line)

Produce **`results/accuracy-report.md`** — the scorecard, re-checked against the honesty bar:

- **The held-out score** — recall on CRITICAL/HIGH and the false-negative rate, from `make eval` on the
  full 50-alert batch (not the demo). This is the measured quality result the whole lab exists to
  produce.
- **The before/after of your prompt change** — the recall you started at, the recall you moved it to,
  and the false-positive cost you paid for it.
- **One documented false call** — the false negative from Step 5, with its text-level cause and the
  FP-economics framing. Cite **OWASP LLM09** for why a confidently-wrong triage is the danger.

**The honesty check (the real finish line):** re-read the report. **If the headline is an accuracy
percentage and the critical-class recall is buried, it's not done** — the number that gates this
pipeline is recall on the alerts that can cost a breach.

---

## Recall check — close the doc, answer from memory (3 min)

1. Why does the demo score not prove the classifier is ready — and what set gives the honest number?
2. Which metric gates this pipeline, and why is accuracy the wrong headline for imbalanced SOC classes?
3. When the triage script can't parse a model response, what must happen — and what's the dangerous
   thing teams do instead?

---

## Deliverables

The triage classifier with its scored eval:

- **`scripts/triage.py`** — with your prompt improvements (few-shot per severity + over-classification bias).
- **`results/accuracy-report.md`** — the scorecard: recall + false-negative rate called out, one
  false-negative analysis, and the before/after of your prompt change.

Commit both. Lab artifacts (raw model-output dumps, intermediate `results/*.json`) stay out of commits.

## Automate & own it

**Required.** Make the eval a *gate run on a cadence* — the per-system version of Module 11's
regression gate. Two parts:

- **Threshold split.** `scripts/triage.py` already takes `--threshold` — run `make triage` with it (or
  invoke the script directly) so HIGH+ alerts land in `results/escalate.json` and the rest in
  `results/below-threshold.json` for the next cycle. Verify the edge case where the model returns an
  invalid severity string: it must default to the next severity level *up*, not crash or silently drop.
- **Recall gate.** Add a `--min-recall` check to `scripts/eval.py`: if recall on CRITICAL/HIGH against
  the held-out set drops below the declared bar (e.g. `0.80`), exit non-zero. This is the monthly
  re-eval as code — point it at next month's freshly labelled alerts and a regression fails loudly.

Have a model draft the filtering, file-writing, and threshold-check logic; **you own** the failure
semantics (parse-fail → human review), the metric choice (gate on recall, not accuracy), and the gate
direction (a missing or errored score must fail *closed*, never silently pass).

## Definition of done (`ai-detection-triage` ✅)

- [ ] `make triage` completed the 50-alert **held-out** batch; you know how many came back `parse_error`.
- [ ] `make eval` printed the confusion matrix + per-class recall; **recall on CRITICAL/HIGH** is recorded.
- [ ] At least one prompt improvement was made and **re-scored on the held-out set**, with before/after recall.
- [ ] `results/accuracy-report.md` records the metrics (recall + FN-rate as headline), one false-negative analysis, and cites **OWASP LLM09**.
- [ ] The `--min-recall` gate exits non-zero when recall drops below the bar (fails closed).
- [ ] You can explain all seven flight-card facts cold.

## Connects forward

The triage output format (structured JSON with `severity · technique · action`) is the **input** for the
SOAR workflow in **Module 08**: the automation playbook reads triage results and triggers containment
for HIGH/CRITICAL alerts. The eval shape you built here — held-out set + scorecard + threshold — is
what [Module 11 (AI Evaluation)](../11-ai-evaluation/README.md) generalizes into a reusable harness, and
what [04 (RAG)](../04-rag/README.md) and [06 (SoC Copilot)](../06-soc-copilot/README.md) borrow for
retrieval and end-to-end answer quality.

## Marketable proof

> "I built and evaluated an AI-assisted alert triage classifier — local model, structured output,
> batch processing, held-out confusion-matrix eval — and I know its recall on critical alerts, its
> false-negative rate, the prompt changes that move them, and the threshold gate that flags a
> regression before an analyst does."

## Stretch

- **Concurrent triage.** Use `ThreadPoolExecutor` to send 3–5 alerts to Ollama in parallel; measure the
  throughput improvement (alerts/min) versus sequential, and record the number.
- **Confidence-weighted routing.** For alerts where the model's output carries `"confidence": "LOW"`,
  route them to a separate human-review queue regardless of predicted severity — and note why that
  closes part of the automation-bias gap.

## References & further reading

- **NVD — CVE-2021-44228 (Log4Shell):** <https://nvd.nist.gov/vuln/detail/cve-2021-44228> — the Apache
  Log4j2 JNDI RCE record (CVSS 10.0); the exploit-string mechanics the T1190 alerts are shaped from.
- **CISA advisory AA21-356A:** <https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-356a> —
  the joint Log4j guidance; skim the IOC and mitigation sections for what defenders actually hunted.
- **MITRE ATT&CK T1190 — Exploit Public-Facing Application:** <https://attack.mitre.org/techniques/T1190/>
  — the technique the Log4Shell initial-access alerts map to; the rest of the corpus uses the techniques
  cited in `data/ground-truth.json`.
- **OWASP Top 10 for LLM — LLM09 (Overreliance):**
  <https://owasp.org/www-project-top-10-for-large-language-model-applications/> — why a confidently-wrong
  triage that de-prioritizes a real alert is the canonical automation-bias failure this eval guards against.
</content>
</invoke>
