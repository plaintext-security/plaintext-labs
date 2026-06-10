# Module 07 — AI-Assisted Detection & Triage

*Module concept · [Go to the hands-on lab →](lab.md)*


**AI-Augmented Security Operations** — *the model doesn't replace the analyst; it handles the repetitive 80% so the analyst focuses on the 20% that matters.*

## Why this matters
A modern SOC generates hundreds to thousands of alerts per shift. The majority are low-confidence,
familiar-pattern events that a skilled analyst evaluates in seconds — but seconds times thousands
adds up to hours of queue-draining toil before anything requiring genuine judgment gets touched.
A local model performing first-pass classification — severity, technique, recommended action — can
compress that queue by routing the clearly-low events to a holding queue and escalating the
high-confidence critical signals immediately. The model doesn't need to be right 100% of the time;
it needs to be right enough to be a useful filter, with a human reviewing anything it flags.

## Objective
Build a batch alert triage script that classifies 50 alerts using a local model, compares the
classifications against a ground-truth label file, and produces a confusion matrix showing where
the model helps and where it misfires.

## The core idea
Alert triage is fundamentally a classification problem: given an alert's text, assign it a severity
(CRITICAL/HIGH/MEDIUM/LOW) and recommend an immediate action. Classification is the task category
where few-shot prompting (Module 03's Pattern 5) is most reliable for local models — the model
pattern-matches against examples rather than reasoning from first principles. The key design
decision in a triage pipeline isn't "which model" — it's "what does failure look like and is it
acceptable?" A false negative (model classifies a CRITICAL alert as MEDIUM) has a very different
cost than a false positive (model classifies a MEDIUM alert as HIGH). Calibrating the prompt to
bias toward over-classification (when uncertain, output HIGH rather than MEDIUM) is the right
choice for a security triage system, unlike most classification tasks where class balance matters.

The output format discipline from Module 03 is non-negotiable here: the triage script parses the
model's output, and a malformed response must be handled explicitly rather than propagated to the
analyst queue as garbage. The right failure mode is "parsing failed → flag this alert for direct
human review → log the raw model output for debugging." A pipeline that silently drops alerts or
logs errors to /dev/null is more dangerous than no pipeline at all.

Throughput constraints make this concrete. If a shift generates 800 alerts and the model processes
5 per minute on the available hardware, the pipeline takes 160 minutes — longer than a shift. The
architectural response is batching and async processing: run the model on the previous hour's
alerts at the start of each hour, so the analyst arrives at a pre-classified queue rather than a
raw feed. The triage pipeline isn't real-time; it's background batch processing, which changes
what "acceptable latency" means. A 30-second response time per alert is fine if the batch ran 50
minutes ago; it's not fine if the analyst is waiting for the result before deciding to escalate.

Quality control for a production triage pipeline means tracking model accuracy over time, not
just at initial validation. Models don't drift (fixed weights), but alert distributions do:
new attack techniques, new tooling, changed environment topology all produce alert patterns the
model hasn't seen in its few-shot examples. Periodic re-evaluation against ground-truth-labeled
alerts from the past month is the discipline that keeps the triage accuracy known and bounded.
Meridian's team runs a monthly accuracy check against 50 human-labeled alerts and flags the
model for prompt review if accuracy drops below 80%.

## Learn (~2 hrs)

**Structured output for triage (~45 min)**
- Review Module 03 — Pattern 4 (Structured Output Alert Triage) before starting the lab.
- [OWASP Top 10 for LLM — LLM09 (Overreliance)](https://owasp.org/www-project-top-10-for-large-language-model-applications/) — the triage pipeline is the canonical overreliance scenario; read the description and mitigations before implementing automated actions on model output.

**Evaluation methodology (~45 min)**
- [Google, "Classification: True vs False, Positive vs Negative" (ML Crash Course)](https://developers.google.com/machine-learning/crash-course/classification/thresholding) — the confusion matrix concepts you'll compute; short, visual, directly applicable.

**Automation patterns (~30 min)**
- [Python `concurrent.futures` documentation](https://docs.python.org/3/library/concurrent.futures.html) — `ThreadPoolExecutor` is how you batch multiple Ollama requests concurrently; read the basic example to understand the map pattern.

## Key concepts
- False-negative cost asymmetry in security triage: bias toward over-classification
- Output format discipline: parse-or-flag, never silently drop
- Batch processing vs. real-time: which latency model fits the use case
- Confusion matrix as ongoing quality control
- Prompt accuracy degrades as alert distributions shift: periodic re-evaluation is mandatory

## AI acceleration
Have a model help write the parsing and confusion-matrix computation code — it's boilerplate.
Your job is to review the failure-handling logic (what happens to an alert where parsing fails?
does it get flagged for human review or silently dropped?) and the bias direction in the prompt
(does the prompt err toward HIGH on uncertainty?). The model writes the plumbing; you own the
failure semantics.
