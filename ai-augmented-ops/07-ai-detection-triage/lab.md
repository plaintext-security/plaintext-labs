# Lab 07 — AI-Assisted Detection & Triage

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/07-ai-detection-triage
make up && make demo
```

**Requirements:** Docker, 4 GB RAM free. No GPU needed.
`make demo` runs the triage script on 5 sample alerts from `data/alerts.jsonl` and shows
the model's classifications alongside the ground-truth labels from `data/ground-truth.json`.
Full 50-alert batch: `make triage`.

## Scenario
Meridian's overnight shift generated 50 alerts. The morning analyst has 90 minutes before the
stand-up. The triage pipeline pre-classifies all 50 and presents only the HIGH/CRITICAL ones
for immediate review. Your job: validate the pipeline's accuracy, understand where it
misfires, and tune the prompt to reduce false negatives (missed critical alerts).

> Everything runs locally. No external targets, no authorization needed.

## Do

1. [ ] `make demo` — watch the model classify 5 sample alerts. For each, note:
   - Predicted severity vs. ground-truth severity
   - Did the model identify the correct ATT&CK technique ID?
   - Did it parse cleanly as JSON, or did the parser have to handle a malformed response?

2. [ ] `make triage` — run the full 50-alert batch. It writes results to
   `results/triage-results.json`. Open it and find:
   - All alerts the model classified as CRITICAL or HIGH
   - Any false negatives (ground-truth HIGH/CRITICAL classified as MEDIUM/LOW)
   - Any false positives (ground-truth LOW classified as HIGH/CRITICAL)

3. [ ] `make eval` — compute the confusion matrix and print accuracy, precision, recall,
   and F1 for each severity class. Record the results in `results/accuracy-report.md`.

4. [ ] Review the prompt in `scripts/triage.py`. Does it bias toward over-classification
   on uncertainty? Does it include a few-shot example of each severity? Modify the prompt
   to include at least one concrete few-shot example per severity level and re-run on the
   5 demo alerts. Did accuracy improve?

5. [ ] Identify one false negative (missed HIGH or CRITICAL) from the full batch results.
   Write a one-paragraph explanation in `results/accuracy-report.md`: what in the alert
   text caused the model to under-classify it, and what prompt change would help?

## Success criteria — you're done when
- [ ] `make demo` runs 5 alerts and prints severity + technique for each.
- [ ] `make triage` completes the 50-alert batch and writes `results/triage-results.json`.
- [ ] `make eval` prints a confusion matrix and accuracy metrics.
- [ ] `results/accuracy-report.md` is filled in with metrics and one false-negative analysis.
- [ ] At least one prompt improvement is made and validated against the demo set.

## Deliverables
`scripts/triage.py` (with your prompt improvements) + `results/accuracy-report.md`. Commit both.

## Automate & own it
**Required.** Extend `triage.py` with a `--threshold` flag: alerts the model classifies below
the threshold severity (e.g. `--threshold HIGH`) are written to `results/below-threshold.json`
for review in the next cycle, while HIGH+ alerts are written to `results/escalate.json` for
immediate analyst review. Have a model draft the filtering and file-writing logic; you review
the edge case where the model returns an invalid severity string (it should default to the next
severity level up, not crash). Commit the extended script.

## AI acceleration
Paste the false-negative alerts (ones the model missed) into a frontier model and ask it to
explain why a small model would under-classify them — what features in the alert text are
ambiguous? Use the explanation to improve your few-shot examples. The frontier model helps
you understand the local model's failure modes.

## Connects forward
The triage output format (structured JSON with severity, technique, action) is the input format
for the SOAR workflow in Module 08: the automation playbook reads triage results and triggers
containment for HIGH/CRITICAL alerts.

## Marketable proof
> "I built and evaluated an AI-assisted alert triage pipeline — local model, structured output,
> batch processing, confusion matrix evaluation — and I know its false-negative rate and the
> prompt changes that improve it."

## Stretch
- Implement concurrent triage: use `ThreadPoolExecutor` to send multiple alerts to Ollama in
  parallel (3–5 workers). Measure the throughput improvement vs. sequential processing.
- Add a "confidence-weighted routing" step: for alerts where the model's structured output
  includes `"confidence": "LOW"`, send them to a separate human-review queue regardless of
  the predicted severity.
