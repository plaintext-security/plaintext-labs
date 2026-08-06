# Lab 02 — Stand It Up, Then Measure It: a local-model baseline

> **Hands-on lab.** Environment: `plaintext-labs/ai-augmented-ops/02-running-local-models`.
> Objective: **stand up a quantised open-weight model as a running, OpenAI-compatible service and
> benchmark it — throughput *and* quality — on Log4Shell triage prompts, on your own hardware.**
> Target: **~90 min**, one finish line. Runs entirely on **local infrastructure you own** (Ollama +
> `tinyllama`, CPU-only). Deliverable: a hardware-justified evaluation report.

---

## ✈ Flight card — the 6 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **Quantisation** shrinks a 7B model from ~14 GB (FP16) to ~4 GB (Q4). | That's the line between "needs a workstation" and "runs on this laptop." |
| 2 | **GGUF + Modelfile** — a quantised-weights container + a small config Ollama pulls and serves. | What `ollama pull` actually fetches; the weights load into RAM behind an HTTP API. |
| 3 | **OpenAI-compatible API on `:11434`** — swap local↔frontier by changing one URL. | You integrate once; the whole track plugs into the service you stand up here. |
| 4 | **Measure throughput *and* quality on YOUR prompts + YOUR hardware.** | 40 tok/s @ 92% beats 8 tok/s @ 94% if your queue drains slower than it grows. A leaderboard can't tell you this. |
| 5 | **Training cutoff is a hard wall.** Model reasons about *technique classes*, not last month's CVE. | Pattern: model classifies the technique; a tool queries the live feed (Modules 04–06). |
| 6 | **What you pull is code.** A malicious GGUF/pickle can run a payload *on load* (nullifAI). | Running a model is a supply-chain trust decision, not just a config change. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea) (quantisation, the serving stack) and
> [the security seam](README.md#the-security-seam-what-you-pull-is-code).

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. Why does **4-bit quantisation** let a 7B model run on a laptop — and what does it cost you?
2. A model **aces a public leaderboard.** Name the one thing that still doesn't tell you, and the
   **two numbers** you have to measure yourself before you'd deploy it for alert triage.

---

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/02-running-local-models
make up && make demo
```

**Requirements:** Docker, ~4 GB RAM free (8 GB recommended for `phi3:mini`), no GPU — all inference
runs on CPU. First `make up` pulls the Ollama image and `tinyllama` (~637 MB); later runs use the
cache. `make demo` runs all five benchmark prompts and prints a latency + throughput table (2–5 min
on CPU). Other targets: `make shell` (a shell in the lab container), `make down` (stop),
`make reset` (tear down volumes and image). Override the model with `OLLAMA_MODEL=phi3:mini make demo`.

Seed file: **`data/benchmark-prompts.txt`** — five realistic SOC triage queries anchored to the
**Log4Shell** exploitation wave (CVE-2021-44228): classify a JNDI/LDAP callback, summarise the CVE,
extract an IOC from an exploit string, recognise a known hash, and generate a Sigma rule. Report
template: **`results/benchmark-results.md`**.

> **▸ On track if:** `curl -s http://localhost:11434/api/tags` returns JSON whose `models` array is
> non-empty and lists your model (Ollama is up and the model pulled — the published host port works).

> **Authorization note.** Everything here runs against **local infrastructure you own** — no external
> targets, no cloud API keys. This is build-and-measure with a live model as the bench. (One real-world
> caution carries over: only `ollama pull` models whose source you'd trust as a dependency — see
> Flight-card #6 and the Stretch scan.)

---

## Build it — read a little, do a little

*The model's exact wording will differ on every run — that's expected. Every rail below checks a
**robust signal** (a JSON field, a `tok/s` number, a non-empty response), never specific generated text.*

### Step 1 — Stand up the running service

**Concept (30 sec):** Flight-card #2–3. `make up` pulls the GGUF + Modelfile, loads the weights into
RAM, and exposes an **OpenAI-compatible REST API** on port 11434 — the service the rest of the track
plugs into.

**Do it:** `make up`, then confirm the service is live and the model is loaded:
```bash
curl -s http://localhost:11434/api/tags | python3 -m json.tool
```

> **▸ On track if:** the JSON `models` array is **non-empty** and contains your model's name. That's
> the running service — reachable on the host, model resident.

### Step 2 — Benchmark throughput on YOUR hardware

**Concept (30 sec):** Flight-card #4. Throughput is **tokens/second**, and the only number that
counts is the one from *your* CPU on *your* prompts — not a model card's.

**Do it:** `make demo`. It sends each of the five prompts to `/api/generate` and prints, per prompt,
a `Latency … | Tokens … | tok/s …` line plus a short answer preview. Copy the latency and throughput
into the table in `results/benchmark-results.md`.

> **▸ On track if:** the demo prints **five** rows, each with a numeric `tok/s > 0` and a non-empty
> answer preview. (The generated text varies run to run; the *number* and its presence are the signal.)

### Step 3 — Read the model card straight from the API

**Concept (30 sec):** Flight-card #1. The quantisation level and parameter count *are* the RAM story —
read them off the running model, not off a blog.

**Do it (host port is published):**
```bash
curl -s http://localhost:11434/api/show -d '{"name":"tinyllama"}' | python3 -m json.tool
```
Find, under `details`, the `parameter_size`, `quantization_level`, and the context length; record
them in the "Model card" section of `results/benchmark-results.md`.

> **▸ On track if:** the JSON has a non-empty `details` object and you can read a `quantization_level`
> (e.g. `Q4_0`) and `parameter_size` (e.g. `1.1B`) out of it.

### Step 4 — Score quality by hand against ground truth

**Concept (30 sec):** Flight-card #4, quality half. A benchmark number is meaningless without the
quality it buys. Mark each answer against the real **Log4Shell** facts (compare to the NVD entry for
CVE-2021-44228), not against how confident the model *sounds*.

**Do it:** for each of the five answers, mark `Correct / Partial / Wrong` in the results table and add
a one-sentence note on what it got right or missed. Prompt 4 is a deliberate trap — that SHA-256 is
the hash of the **empty file**; note whether the model claims it's malware. This by-hand pass is the
seed of the scored, held-out eval you build in **Module 11**.

> **▸ On track if:** all five rows carry a quality mark + a why-line, and you can name **at least one**
> place the model drifts from NVD ground truth **without hedging** (confidence ≠ accuracy — the whole point).

### Step 5 — (optional) Compare a larger model

**Concept (30 sec):** the throughput↔quality trade, made concrete. A bigger model usually answers
better and slower; whether that's worth it depends on your queue.

**Do it (needs ~2 GB more RAM):** `OLLAMA_MODEL=phi3:mini make demo`, then fill the comparison table.
Does the throughput *drop* buy enough quality *lift* for this workload?

> **▸ On track if:** the comparison table has both models' `tok/s` for at least one prompt and a
> one-line verdict on whether the trade is worth it here.

---

## Prove the control (your finish line)

Complete **`results/benchmark-results.md`** — the deliverable, re-checked against the honesty bar:

- **Model card** — parameters, quantisation, context length, Ollama image tag (from Step 3).
- **Benchmark table** — all five prompts with latency, `tok/s`, and a `Correct / Partial / Wrong`
  quality mark + note (Steps 2 & 4).
- **Recommendation** — one paragraph: which model + config you'd run for this team's alert-triage
  pipeline, and why. **Cite a concrete `tok/s` number from your own run** and at least one qualitative
  finding. Reference the Module 01 routing decision (why this tier is Local).

**The honesty check (the real finish line):** the recommendation must stand on **your measured
number**, not a published benchmark. If you can't point to a `tok/s` figure you observed, it's not done.

---

## Recall check — close the doc, answer from memory (3 min)

1. Why does 4-bit quantisation fit a 7B model on a laptop — and what does it cost?
2. The **two numbers** you must measure yourself, and why a leaderboard score isn't enough to deploy.
3. What actually ran when you executed `ollama pull` — and why the **nullifAI** finding makes
   "just download the GGUF" a supply-chain decision, not a config step.

---

## Deliverables

- **`results/benchmark-results.md`** — your completed evaluation (portfolio artifact: the technical
  evidence behind the local-inference infrastructure decision).
- **`benchmark.py`** — the reusable measurement (see *Automate & own it*).

Commit both. *(Lab artifacts — model weights, raw API dumps — stay out of commits.)*

## Automate & own it

**Required.** Write `benchmark.py` — reads `data/benchmark-prompts.txt`, sends each prompt to the
Ollama API, records latency and token count (`eval_count`), and writes a Markdown table to stdout. It
must accept `--model` and `--host` arguments. Have a model draft the HTTP client and formatting; then
**you** review and add the error handling it omits — at minimum: the model isn't pulled yet (404 /
empty `eval_count`), Ollama unreachable (connection refused), and a per-request timeout — each exiting
non-zero with a clear message. Run it and confirm it reproduces the table `make demo` prints. Commit
it — this is the throughput half of "measure on your own hardware," made repeatable. (The quality half
becomes the scored, held-out eval in Module 11.)

> **▸ On track if:** `python3 benchmark.py --model tinyllama --host http://localhost:11434` prints a
> five-row table and **exits 0**; run it with Ollama stopped and it **exits non-zero** with a readable
> error instead of a stack trace.

## Definition of done (`running-local-models` ✅)

- [ ] `make up` succeeded and `curl …/api/tags` lists the model (the OpenAI-compatible service is live).
- [ ] `make demo` produced latency + `tok/s` for all five prompts, recorded in `results/benchmark-results.md`.
- [ ] Each answer is marked `Correct / Partial / Wrong` with a why-line (your by-hand quality pass).
- [ ] Model-card section filled from `/api/show` (params, quantisation, context length).
- [ ] Recommendation cites a concrete `tok/s` number **from your own run**.
- [ ] `benchmark.py` reproduces the demo table, handles the failure cases, and exits non-zero on error.
- [ ] You can explain all six flight-card facts cold — including why `ollama pull` is a trust decision.

## Connects forward

The service you stand up here is the inference engine for the **RAG system in Module 04**, the
**triage script in Module 07**, and the **attack surface in Module 10**. The by-hand quality pass in
Step 4 is the seed of **Module 11 (AI Evaluation & Observability)**, which turns "I eyeballed the
answers" into a held-out test set, a scorecard, and a regression gate. And Flight-card #6 (what you
pull is code) is the model-supply-chain thread **Module 09 (Securing the AI You Run)** picks up.
Knowing this model's throughput and quality ceiling now prevents surprises later.

## Marketable proof

> "I can deploy and benchmark a local language model, measure its throughput and quality on
> domain-specific prompts on my own hardware, and produce a hardware-justified recommendation for or
> against local inference in a security operations context — and I treat the model itself as a
> supply-chain dependency to be vetted before it's loaded."

## Stretch

- **Vet what you load.** Before pulling a *community* GGUF/pickle, scan it with a tool like `modelscan`
  or `picklescan` and note what it flags — the practitioner control against the nullifAI class of attack.
- **Load test.** Fire 10 concurrent requests at the API and measure how throughput degrades under
  concurrency — models a multi-analyst SOC hitting one local model at once.
- **Custom Modelfile.** Wrap `tinyllama` with a security-analyst system prompt baked in via
  `ollama create`, and confirm the system prompt persists across calls without being sent each time.
