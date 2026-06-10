# Module 09 — Detection-as-Code Pipelines

*Module concept · [Go to the hands-on lab →](lab.md)*


**Security Automation** — *a detection that isn't tested isn't a detection — it's a guess with a YAML file.*

## Why this matters
Track 02 (Defensive) introduced Sigma rules and detection-as-code. This module is the
engineering layer on top: the CI pipeline that lints every rule before it merges, the pytest
suite that proves each rule fires on known-bad events and ignores known-good ones, and the gate
that fails the build when a broken rule appears. Without this pipeline, detection-as-code is
version control theater — the rules are in git, but nobody tested them.

## Objective
Build a CI pipeline that lints five Sigma rules with `sigma-cli`, runs `pytest` detection tests
against event JSONL, and fails on a broken rule — demonstrating that a bad detection cannot merge
without the CI gate catching it.

## The core idea
A Sigma rule CI pipeline has two stages: **syntax validation** and **detection testing**.
Syntax validation (`sigma check`) catches malformed YAML, unknown fields, and invalid detection
condition syntax before the rule is compiled to a SIEM query. Detection testing goes further:
it proves the rule's *intent* — that the rule fires on the attack event and does not fire on
the benign baseline. Syntax can be valid and intent can be wrong; both gates are needed.

`pytest` for detection testing is a pattern worth understanding deeply. Each test function
loads a specific Sigma rule, loads a specific event (or a baseline of benign events), runs a
matcher, and asserts the expected outcome. `pytest.parametrize` lets you express this as a
table: for each `(rule, event, expected)` triple, one test case. The table is the contract —
it documents exactly what each rule is supposed to detect and what it's supposed to ignore.
Any rule change that breaks a test is a change that needs explicit re-approval.

The CI gate shape: `sigma check` exits 1 on a broken rule; `pytest` exits 1 on a failing test;
the pipeline `&&`-chains them so either failure blocks the merge. The key discipline is writing
the test *before* the rule (or at the same time) — a rule merged without a test is a rule that
can drift silently. Require tests in the PR review as you would require tests for any production
code change.

False-positive testing is the part most detection pipelines skip and the part that matters most.
Writing a test that proves a rule *fires* is easy; writing a test that proves a rule does *not*
fire on a benign sample is what separates a precise detection from one that generates alert
fatigue. For each rule, include at least one "should not match" test case using a realistic
benign event — a legitimate PowerShell script, a known-good backup process, a normal scheduled
task. The FP test is the scar tissue of production experience — it documents the false positive
you already investigated and doesn't want to see again.

## Learn (~2 hrs)

**sigma-cli (~1 hr)**
- [sigma-cli — SigmaHQ](https://github.com/SigmaHQ/sigma-cli) — read the README through the "Usage" section; understand `sigma check`, `sigma convert`, and how to point it at a rules directory.
- [Sigma rule specification — SigmaHQ wiki](https://github.com/SigmaHQ/sigma/wiki/Specification) — skim the "Detection" section specifically; understanding what `sigma check` validates helps you write rules that pass it.

**pytest for detection testing (~1 hr)**
- [pytest — official documentation, "How to parametrize fixtures and test functions"](https://docs.pytest.org/en/stable/how-to/parametrize.html) — the parametrize pattern is the core of detection test tables; read the full section.
- [Detection testing with pytest — SpecterOps blog (Kyle Ehmke)](https://posts.specterops.io/detection-testing-with-pytest-ee8e4d58cb0b) — a practical walkthrough of the exact pattern used in this lab; read before the lab.

## Key concepts
- Two-stage gate: `sigma check` (syntax) + `pytest` (intent)
- Test table: `(rule, event, expected_match)` parametrized — the contract for each detection
- False-positive tests: "should not match" cases are as important as "should match" cases
- Failing CI on broken rules: the gate that makes detection-as-code real
- Tests before merge: same discipline as application code

## AI acceleration
A model writes Sigma rules quickly and usually syntactically correctly. Ask it to also write the
pytest test for each rule — including a false-positive test case. The FP test is where the model
struggles: it will often generate a test case that is also malicious rather than genuinely benign.
Correct the FP test case with a realistic benign event from `data/tests/` and document why the
model's version was wrong.
