# Lab 07 — AI-Assisted Detection & Triage

*Hands-on lab · [← Back to the module concept](README.md)*

**Type:** Eval Harness — the deliverable is the triage classifier *plus its scored eval* (a held-out
labelled set → confusion matrix → a threshold the score must hold). This is the per-system eval that
[Module 11](../11-ai-evaluation/README.md) generalizes into a reusable harness.

## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/07-ai-detection-triage
make up && make demo
```

**Requirements:** Docker, 4 GB RAM free. No GPU needed.
`make demo` runs the triage classifier on 5 sample alerts from `data/alerts.jsonl` and shows
the model's classifications alongside the ground-truth labels from `data/ground-truth.json`.
Full 50-alert batch: `make triage`.

## Scenario
The overnight shift generated 50 alerts. The morning analyst has 90 minutes before the
stand-up. The triage classifier pre-classifies all 50 and presents only the HIGH/CRITICAL ones
for immediate review. Your job: build the classifier's **eval** — score it against the held-out
ground-truth labels, read the confusion matrix to find where it misfires, and tune the prompt to
reduce false negatives (missed critical alerts) without flooding the queue.

> Everything runs locally. No external targets, no authorization needed.

## Do

1. [ ] `make demo` — watch the model classify 5 sample alerts. For each, note:
   - Predicted severity vs. ground-truth severity
   - Did the model identify the correct ATT&CK technique ID?
   - Did it parse cleanly as JSON, or did the parser have to handle a malformed response?

2. [ ] `make triage` — run the full 50-alert batch. It writes results to
   `results/triage-results.json`. These 50 are your **held-out set** — the prompt was tuned on the
   demo alerts, so this is the honest score. Open it and find:
   - All alerts the model classified as CRITICAL or HIGH
   - Any false negatives (ground-truth HIGH/CRITICAL classified as MEDIUM/LOW)
   - Any false positives (ground-truth LOW classified as HIGH/CRITICAL)

3. [ ] `make eval` — score the held-out batch into the **confusion matrix**: accuracy, precision,
   recall, and F1 per severity class. Record the results in `results/accuracy-report.md`, and call
   out the **recall on CRITICAL/HIGH and the false-negative rate** as the load-bearing numbers — not
   accuracy. (Accuracy can look great while the rare critical misses are exactly what it's hiding.)

4. [ ] Review the prompt in `scripts/triage.py`. Does it bias toward over-classification
   on uncertainty? Does it include a few-shot example of each severity? Modify the prompt
   to include at least one concrete few-shot example per severity level and re-run. Re-score with
   `make eval`: did recall on CRITICAL/HIGH improve, and at what cost in false positives? Record the
   before/after numbers — this is the recall/FP knee you are tuning deliberately.

5. [ ] Identify one false negative (missed HIGH or CRITICAL) from the full batch results.
   Write a one-paragraph explanation in `results/accuracy-report.md`: what in the alert
   text caused the model to under-classify it, and what prompt change would help? Frame the cost in
   FP-economics terms — what does this one miss cost versus the false alarms you'd accept to catch it?

## Success criteria — you're done when
- [ ] `make demo` runs 5 alerts and prints severity + technique for each.
- [ ] `make triage` completes the 50-alert held-out batch and writes `results/triage-results.json`.
- [ ] `make eval` prints a confusion matrix and per-class recall/precision/F1.
- [ ] `results/accuracy-report.md` records the metrics (recall + FN-rate called out), one false-negative analysis, and the before/after of your prompt change.
- [ ] At least one prompt improvement is made and re-scored against the held-out set (not just the demo set).

## Deliverables
The triage classifier with its scored eval: `scripts/triage.py` (with your prompt improvements) +
`results/accuracy-report.md` (the scorecard). Commit both. Lab artifacts (raw model output dumps,
intermediate JSON) stay out of commits.

## Automate & own it
**Required.** Make the eval a *gate run on a cadence*, the per-system version of Module 11's
regression gate. Two parts:
- Extend `triage.py` with a `--threshold` flag: alerts the model classifies below the threshold
  severity (e.g. `--threshold HIGH`) are written to `results/below-threshold.json` for the next
  cycle, while HIGH+ alerts go to `results/escalate.json` for immediate review. Review the edge case
  where the model returns an invalid severity string — it should default to the next severity level
  *up*, not crash.
- Add a `--min-recall` check to `make eval`: if recall on CRITICAL/HIGH against the held-out set
  drops below the declared bar (e.g. 0.80), exit non-zero. This is the monthly re-eval as code — run
  it on next month's freshly labelled alerts and a regression fails loudly instead of silently.

Have a model draft the filtering, file-writing, and threshold-check logic; you own the failure
semantics (parse-fail → human review), the metric choice (gate on recall, not accuracy), and the
gate direction (a missing or errored score must fail *closed*, never silently pass).

## AI acceleration
Paste the false-negative alerts (ones the model missed) into a frontier model and ask it to
explain why a small model would under-classify them — what features in the alert text are
ambiguous? Use the explanation to improve your few-shot examples. The frontier model helps
you understand the local model's failure modes — but you label and verify each example yourself,
because a model labelling its own held-out set is the contamination the eval is meant to catch.

## Connects forward
The triage output format (structured JSON with severity, technique, action) is the input format
for the SOAR workflow in Module 08: the automation playbook reads triage results and triggers
containment for HIGH/CRITICAL alerts. The eval shape you built here — held-out set + scorecard +
threshold — is what [Module 11](../11-ai-evaluation/README.md) generalizes into a reusable harness,
and what [04 (RAG)](../04-rag/README.md) and [06 (SoC Copilot)](../06-soc-copilot/README.md) borrow
for retrieval and end-to-end answer quality.

## Marketable proof
> "I built and evaluated an AI-assisted alert triage classifier — local model, structured output,
> batch processing, held-out confusion-matrix eval — and I know its recall on critical alerts, its
> false-negative rate, the prompt changes that move them, and the threshold gate that flags a
> regression before an analyst does."

## Stretch
- Implement concurrent triage: use `ThreadPoolExecutor` to send multiple alerts to Ollama in
  parallel (3–5 workers). Measure the throughput improvement vs. sequential processing.
- Add a "confidence-weighted routing" step: for alerts where the model's structured output
  includes `"confidence": "LOW"`, send them to a separate human-review queue regardless of
  the predicted severity.
