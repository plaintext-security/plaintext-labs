# Module 02 — Running Local Models

*Module concept · [Go to the hands-on lab →](lab.md)*


**AI-Augmented Security Operations** — *a model you can't explain is a dependency you can't audit; running it yourself is where that audit starts.*

## Why this matters
Sending sensitive telemetry to a hosted model is often a non-starter — data residency requirements,
security classification policies, and network segmentation all push toward running the model on
infrastructure you control. Ollama made this accessible: a single binary that pulls a model, starts
an OpenAI-compatible REST API on localhost, and serves inference without a PhD in CUDA. Understanding
how that serving layer actually works — what the model weights are, why quantisation matters, how
throughput scales with hardware — is the foundation for making the local tier reliable rather than
just demo-ware.

## Objective
Run a quantised open-weight model locally via Ollama, measure its throughput on a set of security
prompts, and articulate the hardware-quality-latency tradeoff in terms a security team can act on.

## The core idea
A language model is, at its core, a very large file of floating-point numbers — the weights — plus
the code that multiplies them together at inference time. The breakthrough that made local inference
practical is **quantisation**: instead of storing each weight as a 32- or 16-bit float, you
represent it in 4 or 8 bits, losing a small amount of numerical precision in exchange for a
dramatic reduction in memory footprint. A 7-billion-parameter model in 16-bit precision needs ~14 GB
of RAM; the same model in 4-bit quantisation fits in ~4 GB. That's the difference between "needs a
high-end workstation" and "runs on a developer laptop." The GGUF format (used by `llama.cpp` and
Ollama) is the container format that packages quantised weights for CPU inference.

Ollama's key abstraction is the **Modelfile** — a small configuration that points at a GGUF base
model and layers in a system prompt, a context size, and any sampling parameters. When you run
`ollama run tinyllama`, you're actually pulling a Modelfile plus a quantised GGUF, starting a
serving process that loads the weights into RAM, and opening an HTTP API on port 11434. The API is
intentionally OpenAI-compatible: the same client code that hits `api.openai.com/v1/chat/completions`
can hit `localhost:11434/v1/chat/completions` with a one-line URL change. This matters for
security tool integration: you write the integration once against the local model, and swapping to
a frontier model is a configuration change, not a code change.

For a security team, the practical axis isn't "which model is smarter" — it's throughput vs. quality
at the task. Throughput is measured in tokens per second; quality is measured empirically against
your actual prompts and use case. A model that generates 40 tokens/second and gets classification
right 92% of the time is useful for alert triage; one that generates 8 tokens/second and gets it
right 94% is not, if your queue grows faster than it's processed. The benchmark isn't a leaderboard
score — it's your prompts, your alerts, your hardware. `llama.cpp`'s `llama-bench` and the simple
timer loop in this lab's `data/benchmark-prompts.txt` give you that measurement directly.

One important operational constraint: models don't update themselves. A local model's knowledge is
frozen at its training cutoff. For threat intelligence — which evolves daily — this means the model
can reason about *technique classes* (phishing, encoded execution, lateral movement) but will not
know about a CVE disclosed last month. The operational pattern at Meridian is "model classifies the
technique; the analyst queries the live threat feed." The model handles the reasoning pattern;
current data comes from tools (more on that in Modules 04–06).

## Learn (~3 hrs)

**How models run locally (~1.5 hrs)**
- [Ollama documentation — Models overview](https://ollama.com/library) — browse the model library to understand the naming convention (`name:size-quantisation`); pay attention to the size column vs. the parameter count.
- [GGUF and the llama.cpp ecosystem (Hugging Face blog)](https://huggingface.co/docs/hub/en/gguf) — explains the GGUF format, quantisation levels (Q4_K_M, Q8_0, etc.), and how to find models. Read the "Quantization" section carefully.
- [llama.cpp README](https://github.com/ggml-org/llama.cpp/blob/master/README.md) — skim the benchmarking section; the `llama-bench` tool is what the lab automates.

**Practical deployment (~1 hr)**
- [Simon Willison, "Run a model with llama.cpp"](https://simonwillison.net/2023/Mar/11/llama/) — short walkthrough that demystifies the whole stack in one read; written in 2023 but the concepts haven't changed.
- [Ollama API reference](https://github.com/ollama/ollama/blob/main/docs/api.md) — the REST API you'll call directly; focus on `/api/generate` and `/api/chat` endpoints.

**Hardware and throughput (~30 min)**
- [Tim Dettmers, "Which GPU for deep learning?"](https://timdettmers.com/2023/01/30/which-gpu-for-deep-learning/) — the most cited practical guide; skim for the memory bandwidth discussion, which explains why VRAM dominates inference speed.

## Key concepts
- Quantisation: how 4-bit weights make 7B models fit on a laptop
- GGUF format and Ollama's Modelfile abstraction
- OpenAI-compatible API: write once, swap endpoint for local-vs-frontier
- Throughput (tokens/sec) vs. quality as the practical evaluation axis
- Training cutoff as a hard limit for threat intel recency

## AI acceleration
Use a model to help you analyse your benchmark results — paste in the throughput numbers and ask
it to explain which tasks benefit from a larger model and which are well-served by the small one.
The model can reason about the tradeoff; you supply the empirical numbers it can't know.
