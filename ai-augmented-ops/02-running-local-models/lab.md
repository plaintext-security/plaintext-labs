# Lab 02 — Running Local Models

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/02-running-local-models
make up && make demo
```

**Requirements:** Docker, 4 GB RAM free minimum (8 GB recommended for `phi3:mini`).
No GPU required — all inference runs on CPU. First run pulls `tinyllama` (~637 MB);
set `OLLAMA_MODEL=phi3:mini` to benchmark a more capable model if you have 8 GB free.

The `make demo` target runs all five benchmark prompts and prints a results table with
latency and token throughput for each. It takes 2–5 minutes on CPU.

## Scenario
Meridian's security team wants to justify local-model infrastructure to their CISO. The
argument isn't just privacy — it's that a local model processing 40 alerts per minute is
operationally useful; one that processes 4 is not. Your job: benchmark the local model
on the five security-domain prompts in `data/benchmark-prompts.txt`, interpret the
throughput vs. quality results, and produce a one-page evaluation report.

> Everything runs locally. No external targets, no cloud API keys required.

## Do

1. [ ] `make demo` and read the benchmark output. For each of the five prompts, record the
   latency (seconds) and throughput (tokens/sec) in `results/benchmark-results.md`.
   The demo script prints these for you — copy them into the table template in that file.

2. [ ] Qualitatively evaluate each answer: is it factually correct, partially correct, or
   wrong? Mark each cell in `results/benchmark-results.md` as Correct / Partial / Wrong
   and add a one-sentence note explaining what the model got right or missed.

3. [ ] `make shell` and call the Ollama API directly to explore the model metadata:
   ```bash
   curl -s http://ollama:11434/api/show -d '{"name":"tinyllama"}' | python3 -m json.tool
   ```
   Find: the model's parameter count, quantisation level, and context length. Write these
   in the "Model card" section of `results/benchmark-results.md`.

4. [ ] Compare to a larger model (optional, requires 8 GB RAM):
   ```bash
   OLLAMA_MODEL=phi3:mini make demo
   ```
   If you have the hardware, run the benchmark again and add a comparison column. Does the
   throughput drop match the quality improvement? Is the tradeoff worth it for these prompts?

5. [ ] Write a one-paragraph "Recommendation" at the bottom of `results/benchmark-results.md`:
   which model and configuration would you recommend for Meridian's alert triage pipeline,
   and why? Cite the throughput number and at least one qualitative quality finding.

## Success criteria — you're done when
- [ ] `results/benchmark-results.md` contains latency and throughput data for all five prompts.
- [ ] Each answer is marked Correct / Partial / Wrong with a one-sentence explanation.
- [ ] The model card section (parameters, quantisation, context length) is filled in.
- [ ] The Recommendation paragraph is written and cites a concrete throughput number.

## Deliverables
`results/benchmark-results.md` (your completed evaluation). Commit it — this is the
technical evidence behind Meridian's infrastructure decision.

## Automate & own it
**Required.** Write `benchmark.py` — a Python script that reads `data/benchmark-prompts.txt`,
sends each prompt to the Ollama API, records latency and token count, and writes a Markdown
table to stdout. The script should accept `--model` and `--host` arguments. Have a model
draft the HTTP client and result-formatting logic; you review the error handling (what happens
if the model isn't pulled yet? if Ollama is unreachable?) and add it. Run the script and
confirm it produces the same table `make demo` shows. Commit it.

## AI acceleration
Paste your benchmark results table into a frontier model and ask it to interpret the
quality/speed tradeoff for a high-volume SOC alert triage use case. Compare its analysis
to your own. Where do they agree? Where does the model offer a dimension you hadn't
considered? Document the differences in the Recommendation paragraph.

## Connects forward
The model you benchmark here is the inference engine for the RAG system in Module 04,
the triage script in Module 07, and the attack surface in Module 10. Understanding its
throughput and quality ceiling now prevents surprises later.

## Marketable proof
> "I can deploy and benchmark a local language model, measure its throughput and quality
> on domain-specific prompts, and produce a hardware-justified recommendation for or
> against local inference in a security operations context."

## Stretch
- Build a simple HTTP load test against the Ollama API (10 concurrent requests) and
  measure how throughput degrades under concurrency. This models a multi-analyst SOC
  where several triage workers hit the same local model simultaneously.
- Explore the Modelfile format: create a custom Modelfile that wraps `tinyllama` with a
  security-analyst system prompt baked in. Pull it with `ollama create` and confirm the
  system prompt persists across calls without being sent in each request.
