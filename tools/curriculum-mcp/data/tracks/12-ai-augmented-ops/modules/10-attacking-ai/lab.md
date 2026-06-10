# Lab 10 — Attacking AI Systems

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/10-attacking-ai
make up && make demo
```

**Requirements:** Docker, 4 GB RAM free. No GPU needed.
`make demo` runs `garak` against the local Ollama model with a focused probe set (injection
and leakage probes only — the full scan takes 30–60 minutes). `make garak-full` runs the
complete probe suite.

> Test prompt-injection and jailbreak techniques only against models and applications
> you own or are authorised to assess. All targets here are local Docker containers.

## Scenario
Before Meridian deploys the SoC Copilot to production, the security team runs a systematic
AI vulnerability scan. Your job: run `garak` and `promptfoo` against the local model, interpret
the findings in the context of a SOC assistant, and produce a threat model document.

## Do

1. [ ] `make demo` — run the fast garak scan (injection + leakage probes). Read the output:
   - Which probe classes ran?
   - What was the pass rate for each probe? (Higher = more of the attacks were blocked)
   - Any probes with a pass rate below 80%? These are findings.
   Copy the summary table into `results/garak-findings.md`.

2. [ ] `make promptfoo-eval` — run the `promptfoo` evaluation against the six test cases in
   `data/attack-prompts.yaml`. For each test case, read:
   - The prompt sent
   - The model's actual output
   - Whether it passed the defined assertion
   Copy any failing assertions into `results/promptfoo-findings.md` and explain why the
   assertion failed.

3. [ ] For each garak finding (probe class with pass rate < 80%), write one paragraph in
   `results/garak-findings.md`:
   - What attack technique does this probe class represent?
   - In the context of a SOC assistant, what could an attacker do if this technique works?
   - What mitigation (from Module 09 or OWASP LLM) applies?

4. [ ] Write `results/threat-model.md` — a structured threat model for the SoC Copilot:
   - **Adversaries**: who would target this system and why?
   - **Assets**: what does the system have that an attacker wants?
   - **Attack surface**: prompt input, tool results, RAG context, model API
   - **Top 3 threats**: with OWASP LLM risk IDs and MITRE ATLAS technique IDs
   - **Mitigations implemented**: reference Modules 05, 09
   - **Residual risk**: what's still open after all mitigations

5. [ ] Add one new test case to `data/attack-prompts.yaml` — a SOC-specific jailbreak attempt
   that isn't covered by the existing six. Run `make promptfoo-eval` and document whether it
   passes or fails.

## Success criteria — you're done when
- [ ] `make demo` completes and prints a garak probe summary.
- [ ] `make promptfoo-eval` runs all test cases and prints pass/fail for each assertion.
- [ ] `results/garak-findings.md` has the summary table and one paragraph per finding.
- [ ] `results/promptfoo-findings.md` has analysis of any failing assertions.
- [ ] `results/threat-model.md` is complete with all five sections.
- [ ] One new test case added to `data/attack-prompts.yaml`.

## Deliverables
`data/attack-prompts.yaml` (with your new test) + `results/garak-findings.md` +
`results/promptfoo-findings.md` + `results/threat-model.md`. Commit all four.

## Automate & own it
**Required.** Write a shell script `scripts/scan.sh` that: (1) runs `garak` with the injection
and leakage probes, (2) runs `promptfoo eval`, (3) extracts failing probes from each output, and
(4) writes a summary `results/scan-summary.txt` with the date, model name, and number of
failing probes from each tool. Have a model draft the grep/jq logic for extracting the
failure count; you review whether it correctly identifies all failure modes (not just "FAIL"
strings). Commit the script.

## AI acceleration
Have a frontier model review your `results/threat-model.md` and suggest threats you haven't
covered. Ask it specifically: "Given this SOC copilot architecture (RAG + MCP + Ollama), what
MITRE ATLAS techniques are not addressed by this threat model?" Add any non-trivial gaps to
the residual risk section.

## Connects forward
This module closes the loop: you built the AI (Modules 01–06), used it (Module 07–08), secured
it (Module 09), and now red-teamed it systematically (Module 10). The track capstone is to take
one tool from the stack, demonstrate a finding against it, and ship a hardened version with a
documented test suite. The threat model from this module is the capstone's starting point.

## Marketable proof
> "I can run systematic LLM security scans using garak (vulnerability scanner) and promptfoo
> (evaluation framework) against locally deployed models, interpret findings in a security
> operations context, and produce a structured threat model for an AI-augmented SOC system."

## Stretch
- Run the full garak probe suite (`make garak-full`) and compare findings to the fast scan.
  Which additional probe classes produce findings? Are any operationally significant for a
  SOC context?
- Configure `promptfoo` to run the evaluation in CI (GitHub Actions): add a step that fails
  the build if any assertion has a pass rate below 90%. This is the regression test discipline
  applied to LLM safety.
