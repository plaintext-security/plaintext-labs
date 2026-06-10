# Lab 09 — Detection-as-Code Pipelines

*Hands-on lab · [← Back to the module concept](README.md)*


## Setup
```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/automation/09-detection-as-code-pipelines
make up        # sigma-cli + pytest in Docker
make demo      # runs sigma check (lint) over data/rules/, then pytest over data/tests/
make shell
make down
```

`data/rules/` contains five Sigma rules: four valid, one deliberately broken (invalid condition
syntax). `data/tests/` contains test event JSONL files and a `conftest.py` that provides a
`match_rule(rule_path, event)` fixture. `make demo` runs `sigma check` (which fails on the
broken rule) and then `pytest` over the test suite.

## Scenario
Meridian's detection engineering team is setting up the CI gate for their Sigma rule repository.
Your task: (1) find and fix the broken rule so `sigma check` passes; (2) write pytest tests for
all five rules including false-positive cases; (3) demonstrate the full CI gate by running both
stages in sequence.

## Do
1. [ ] `make demo` — watch it fail on the broken rule. Read the `sigma check` error carefully:
   which rule is broken and what is the syntax error?
2. [ ] Open the broken rule in `data/rules/` and fix the condition syntax. Run `sigma check
   data/rules/` — confirm it exits 0.
3. [ ] Read `data/tests/conftest.py` — understand the `match_rule(rule_path, event_path)` fixture
   and how it returns `True`/`False`.
4. [ ] Write `data/tests/test_detections.py` with `pytest.parametrize` test cases for all five
   rules. For each rule, include:
   - One `(rule, malicious_event, True)` — rule fires on the attack.
   - One `(rule, benign_event, False)` — rule does not fire on the benign baseline.
   Event JSONL files are in `data/tests/events/`; each file is named for its scenario.
5. [ ] Run `pytest data/tests/ -v` — all 10 test cases should pass (5 rules × 2 cases).
6. [ ] Deliberately break one rule (change a field name in the detection section to something
   invalid) and rerun `sigma check` — confirm it exits 1. Revert the break.
7. [ ] Write `ci-gate.sh`:
   ```bash
   sigma check data/rules/ && pytest data/tests/ -q
   ```
   Run it — confirm it exits 0 on clean rules and 1 when a rule is broken.

## Success criteria — you're done when
- [ ] All five rules pass `sigma check`.
- [ ] All 10 pytest cases (5 match + 5 no-match) pass.
- [ ] `ci-gate.sh` exits 1 on a broken rule and 0 when everything is clean.
- [ ] You can explain what each false-positive test case proves.

## Deliverables
Fixed `data/rules/<broken-rule>.yml` + `data/tests/test_detections.py` + `ci-gate.sh`. Commit all.

## Automate & own it
**Required.** Write a GitHub Actions workflow `data/.github/workflows/sigma-ci.yml` that runs
`sigma check` and `pytest` on every push to `main` and every PR. Have a model draft it; review:
Does it pin the Docker image version? Does it fail the PR on a broken rule? Commit the workflow.

## AI acceleration
Ask a model to write the false-positive test cases for each rule. Review each one: is the benign
event genuinely benign? Would the rule actually fire on it, making the test wrong? The model's
FP cases are often subtly malicious — they match the rule's condition even though they're
supposed to prove the rule doesn't fire. Catching this is the skill the module is teaching.

## Connects forward
This pipeline is the complete implementation of detection-as-code: rules in git, syntax-checked,
intent-tested, CI-gated. Combined with module 08 (SOAR), this is the full defensive automation
stack — rules that detect, playbooks that respond, pipelines that prevent regressions.

## Marketable proof
> "I gate Sigma rule changes in CI with a two-stage pipeline: sigma check for syntax, pytest for
> intent, including false-positive test cases — a broken detection cannot merge without the CI
> catching it."

## Stretch
- Add `sigma convert -t splunk` as a third CI stage that compiles each rule and fails if
  conversion produces an empty query — catching rules that are syntactically valid but logically
  empty after compilation.
- Write a sixth rule from scratch for a new ATT&CK technique and add its test cases before the
  rule is complete — test-driven detection engineering.
