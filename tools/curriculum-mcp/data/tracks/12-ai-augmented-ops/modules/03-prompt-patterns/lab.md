# Lab 03 — Prompt Patterns for Security

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/03-prompt-patterns
make up && make demo
```

**Requirements:** Docker, 4 GB RAM free. No GPU needed.
`make demo` starts Ollama with `tinyllama` and runs one worked-example pattern
(few-shot IOC classification) so you can see the pattern-then-validate loop before
you start writing your own.

## Scenario
Meridian's security team wants to systematise how they prompt local models. Before
anyone integrates a model into a pipeline, every prompt needs to be validated against
known-good and known-bad cases and documented in the team's pattern library. Your job
is to validate three patterns from `data/prompt-patterns.md` against the running model,
document what worked and what failed, and add one new pattern you write yourself.

> Everything runs locally. No cloud API keys required.

## Do

1. [ ] `make demo` — watch the few-shot IOC classification pattern run. The demo prints
   the prompt, the raw model output, and whether it parsed as valid JSON. Read the prompt
   text carefully: where is the few-shot structure? Why is JSON output specified in the
   instructions rather than just asked for?

2. [ ] Open `data/prompt-patterns.md` and read all eight patterns. Pick **three** to
   validate: one that uses structured output (Pattern 3 or 4), one that uses chain-of-thought
   (Pattern 2), and one other of your choice.

3. [ ] For each of your three chosen patterns, run it against the local model:
   ```bash
   make shell
   # then use the Ollama API or the helper script:
   python3 scripts/run-pattern.py --pattern 2
   ```
   Record the raw output in `results/pattern-validation.md`.

4. [ ] For each run, classify the output against the three failure modes:
   - **Hallucination**: did the model fabricate any fact? (Check IOC values, CVE IDs, etc.)
   - **Off-format**: did the output match the expected structure/schema?
   - **Overconfidence**: did the model state something confidently that it shouldn't know?

5. [ ] Write one **new pattern** of your own for a security task not covered by the eight
   in `data/prompt-patterns.md`. Add it to the file as Pattern 9, following the same
   template (name, use case, template text, example, expected failure modes). Run it and
   validate it.

## Success criteria — you're done when
- [ ] `results/pattern-validation.md` contains raw output and failure-mode analysis for
  three patterns from `data/prompt-patterns.md`.
- [ ] At least one failure mode (hallucination, off-format, or overconfidence) was observed
  and documented.
- [ ] Pattern 9 is written in `data/prompt-patterns.md`, run against the model, and its
  output is included in `results/pattern-validation.md`.

## Deliverables
`data/prompt-patterns.md` (with your Pattern 9 added) + `results/pattern-validation.md`
(your validation notes). Commit both — these become Meridian's team prompt library.

## Automate & own it
**Required.** Write `scripts/validate-patterns.py` — a script that runs all patterns in
`data/prompt-patterns.md` against the Ollama API, checks any JSON-output patterns against
their expected schema using Python's `json` module, and prints PASS/FAIL for each. Have a
model draft the schema-checking logic; you add the check that catches off-format output
(e.g. model wraps JSON in a markdown code block — your parser must handle that). Run it and
confirm at least one FAIL fires on a real bad output. Commit it.

## AI acceleration
Use a frontier model to help draft your Pattern 9 template and example. Then run it against
`tinyllama` — the two models may respond very differently to the same prompt. Document the
gap. This is the "test on the target model" discipline that makes prompts portable.

## Connects forward
The structured-output patterns from this module are the interface contract for Module 07's
alert triage pipeline: the triage script relies on the model returning machine-parseable JSON.
If a prompt fails the format check, the pipeline rejects it — which is exactly the behaviour
you want.

## Marketable proof
> "I can write and validate security-specific prompt patterns — structured output for IOC
> extraction, chain-of-thought for threat modelling, few-shot for classification — and I
> know how to test them for hallucination, off-format output, and overconfidence."

## Stretch
- Add a `--model` flag to `scripts/validate-patterns.py` and run the same validation against
  two models side-by-side. Which patterns degrade most on the smaller model?
- Implement a simple confidence-rating check: after each prompt, send a follow-up asking the
  model to rate its confidence on a 1–5 scale. Correlate low confidence with observed
  hallucinations in your validation notes.
