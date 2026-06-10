# Module 03 — Prompt Patterns for Security

*Module concept · [Go to the hands-on lab →](lab.md)*


**AI-Augmented Security Operations** — *the prompt is the program; write it like one.*

## Why this matters
Getting a model to produce useful output isn't magic — it's engineering. Security tasks have
specific failure modes that general-purpose prompting advice doesn't cover: a threat model
prompt that produces a vague list instead of a prioritised risk ranking, an IOC extraction
prompt that hallucinates hashes that aren't in the text, a triage prompt that confidently
misclassifies a novel technique it's never seen. The difference between a model that
accelerates your work and one that introduces noise into your analysis is almost entirely in
how you wrote the prompt. This module makes that engineering explicit.

## Objective
Build a reusable library of eight security-specific prompt patterns and validate three of
them against a running local model, documenting where each pattern succeeds, where it fails,
and what you'd tune.

## The core idea
A prompt is a program — it has inputs, transformation logic, and expected outputs, and like
any program it should be written precisely and tested empirically. The analogy breaks down in
one critical way: a program either compiles or it doesn't; a prompt always produces *something*,
which means a bad prompt is far harder to detect than a broken function. This is the central
hazard of prompting: confident wrong output looks the same as confident right output. The
practitioner skill isn't creativity — it's the ability to specify the output format tightly
enough that a wrong answer is obviously wrong, and to test the prompt against cases where
failure is expected.

Security prompts fail in characteristic ways that generalist prompting guides don't address.
**Role prompting** ("You are a malware analyst...") works well for shaping vocabulary and
reasoning style, but it doesn't constrain factual accuracy — a model playing a malware analyst
will still hallucinate CVE IDs. **Chain-of-thought** ("think step by step") genuinely improves
multi-step reasoning tasks like threat modelling, but the intermediate steps can be wrong in
ways that don't surface in the conclusion — you have to read the chain, not just the answer.
**Structured output** (asking for JSON or a fixed table) is the single most reliable way to
make model output machine-consumable, but models will silently drop fields or invent them if
the schema isn't enforced by the parsing layer. **Few-shot examples** reduce hallucination
on classification tasks more reliably than any other technique — the model pattern-matches
against your examples rather than generalising from training, which is exactly what you want
for IOC classification.

The failure mode taxonomy is as important as the pattern library. Hallucination (fabricated
facts), off-format output (valid JSON with wrong schema), and overconfidence (high-certainty
wrong answers) each require a different mitigation: hallucination responds to few-shot and
constrained output; off-format responds to schema validation in the calling code;
overconfidence responds to asking the model to rate its own confidence and flag when a task
is outside its knowledge. None of these mitigations eliminate the error — they make failures
legible so a human reviewer catches them before they propagate.

The operational implication is that prompt patterns are not one-time decisions. As the model
changes (different version, different quantisation, different context window), the same prompt
can produce different results. Prompt libraries belong in version control, tested with the
same discipline as code — and the tests run against real model outputs, not static fixtures.
Meridian's security team tracks prompt patterns in the same git repository as their detection
rules, with a CI job that runs each prompt and checks the output against a validation schema.
If a model upgrade breaks a prompt's output format, CI catches it before an analyst gets a
garbled triage result.

## Learn (~2.5 hrs)

**Prompting fundamentals (~1 hr)**
- [Prompt Engineering Guide (DAIR.AI)](https://www.promptingguide.ai/) — the canonical community reference; read "Basic Prompting," "Zero-Shot," "Few-Shot," and "Chain of Thought" sections. Skip the fine-tuning material for now.
- [OpenAI Cookbook — techniques to improve reliability](https://developers.openai.com/cookbook/articles/techniques_to_improve_reliability) — short, practical, model-agnostic; the "decompose complex tasks" and "structured output" sections directly apply to SOC workflows.

**Security-specific application (~1 hr)**
- [OWASP Top 10 for LLM Applications — LLM01 (Prompt Injection)](https://owasp.org/www-project-top-10-for-large-language-model-applications/) — understanding injection is inseparable from writing injection-resistant prompts; read the description and examples.
- [Simon Willison, "Prompt injection attacks against GPT-3"](https://simonwillison.net/2022/Sep/12/prompt-injection/) — the original framing of prompt injection from one of the problem's earliest describers; short and directly actionable.

**Structured output and validation (~30 min)**
- [Ollama structured output docs](https://ollama.com/blog/structured-outputs) — how to request JSON output from Ollama with a schema; the technique that makes model output machine-consumable without string parsing.

## Key concepts
- The prompt as a program: precise specification, empirical testing, version control
- Role prompting, chain-of-thought, structured output, few-shot — when each earns the cost
- Security failure modes: hallucination, off-format output, overconfidence
- Structured output + schema validation as the machine-consumable interface
- Prompts belong in git: version-controlled, tested, reviewed like detection rules

## AI acceleration
Have a model help you write prompts — meta-prompting ("write me a few-shot prompt for IOC
extraction") is genuinely productive. Then test every generated prompt against the model it's
targeting: a prompt that works on GPT-4o may perform differently on `tinyllama`. You review
the output for each of the three failure modes before calling the pattern "validated."
