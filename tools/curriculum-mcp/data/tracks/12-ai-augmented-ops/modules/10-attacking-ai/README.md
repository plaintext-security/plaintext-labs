# Module 10 — Attacking AI Systems

*Module concept · [Go to the hands-on lab →](lab.md)*


**AI-Augmented Security Operations** — *red-teaming AI is the same discipline as red-teaming anything: systematic coverage, documented findings, and a repeatable test suite.*

## Why this matters
Module 09 taught you to attack specific, known vulnerabilities in your copilot. This module
takes the complementary approach: systematic scanning. `garak` is to LLMs what a vulnerability
scanner is to web applications — it runs a large library of probe classes (prompt injection,
jailbreaks, encoding attacks, data extraction, model hallucination induction) against a target
model API and reports which probes succeeded. `promptfoo` takes the evaluation approach: define
expected outputs for a set of prompts, run the model, and report where actual output diverges
from the spec. Together they give you coverage you can't achieve with manual testing alone.

## Objective
Run `garak` and `promptfoo` against the local Ollama model from Module 01, document the findings,
and write a threat model for the model's attack surface in a SOC context.

## The core idea
Automated LLM security scanning differs from traditional vulnerability scanning in one important
way: the results are probabilistic, not binary. A CVE scanner either finds the CVE or it doesn't.
`garak` finds that a probe succeeds N% of the time — because the same prompt, sent to the same
model with the same temperature setting, can produce different outputs on different runs. The
discipline of LLM security evaluation is therefore statistical: run each probe class at least 10
times, report pass rate, and classify as a finding only when pass rate exceeds a threshold you
set (e.g. > 20% success). A probe that fires once in 100 runs is noise; one that fires 80 times
is a vulnerability.

`garak` organises its attack library into probe classes (categories of attack) and detectors
(criteria for judging whether an attack succeeded). The probe classes most relevant to a SOC
context are: `dan` (Do Anything Now jailbreaks — testing the model's content filter bypass
resistance), `injection` (prompt injection techniques), `leakage` (system prompt extraction —
does the model reveal its instructions when asked?), and `malwaregen` (does the model generate
malicious content when manipulated?). Not all probe classes are appropriate for all contexts;
for a SOC assistant, the most operationally relevant findings are jailbreaks that could allow
an attacker to override the analyst role instruction, and leakage that could reveal the system
prompt structure to an attacker planning a more targeted injection.

`promptfoo` operates at a different layer: it's an evaluation framework that lets you define
a test suite of expected behaviours. A `promptfoo` test for a SOC assistant might specify:
"Given this alert text, the model's output must contain a severity field and must not contain
any domain name not present in the input." Running this test suite on every model upgrade or
prompt change gives you a regression test that catches behaviour changes before they reach
production. This is the LLM equivalent of a CI unit test — the discipline that makes "AI
authors → you review → you own it" sustainable at scale.

The threat model for a SOC assistant model is the synthesis of these two tools' findings with
the context from Module 09's manual attacks. A threat model for an LLM is a structured document
that answers: who are the adversaries (insider, external attacker, malicious alert data),
what do they want (reclassify alerts, extract the system prompt, cause false containment),
what's the attack surface (prompt input, tool results, RAG context, model weights), and what
mitigations reduce each risk to acceptable levels. This document — not the test results in
isolation — is what you hand to a CISO asking whether the copilot is safe to deploy.

## Learn (~2.5 hrs)

**garak (~1 hr)**
- [garak — LLM vulnerability scanner (GitHub)](https://github.com/NVIDIA/garak) — the README covers installation, supported generators (including Ollama), and probe classes. Skim the probe library list to understand what's being tested.
- [garak documentation — generators and probes](https://docs.garak.ai/garak) — focus on the Ollama generator configuration and the probe class descriptions for `injection`, `dan`, and `leakage`.

**promptfoo (~1 hr)**
- [promptfoo — Getting started](https://www.promptfoo.dev/docs/getting-started/) — the config file format and the basic `promptfoo eval` workflow; skim the YAML config example.
- [promptfoo — Security testing](https://www.promptfoo.dev/docs/red-team/) — the LLM red-team evaluation features; read for the "assertions" that define what a safe response looks like.

**LLM threat modelling (~30 min)**
- [MITRE ATLAS — Adversary threat matrix for AI](https://atlas.mitre.org/) — the techniques catalogue for AI systems; this is the structured vocabulary for your threat model.
- [OWASP LLM Top 10 — all 10 risks](https://owasp.org/www-project-top-10-for-large-language-model-applications/) — read all 10 entries end-to-end as a checklist for your threat model.

## Key concepts
- LLM security scanning is probabilistic: pass rate over N runs, not binary
- garak probe classes: injection, dan (jailbreak), leakage (system prompt extraction), malwaregen
- promptfoo as a regression test suite: expected-output assertions run on every prompt change
- Threat model for an LLM: adversaries, goals, attack surface, mitigations, residual risk
- Statistical threshold for "finding": > 20% probe success rate is a vulnerability

## AI acceleration
Have a model help write the `promptfoo` assertion logic — describe the expected behaviour in
natural language and ask it to translate to YAML assertion syntax. Then review every assertion:
does it actually catch the failure mode it's meant to? A test that always passes regardless of
model output isn't a test. The model writes the YAML; you verify the assertions are meaningful.
