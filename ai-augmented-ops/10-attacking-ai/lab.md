# Lab 10 — Red-team the copilot, then freeze it into a regression eval

> **Hands-on lab.** Environment: `plaintext-labs/ai-augmented-ops/10-attacking-ai`.
> Objective: **run a systematic AI red-team of the SoC copilot — broad statistical coverage with
> `garak`, expected-output assertions with `promptfoo` — then freeze the result into a CI regression
> gate that goes red when a blocked attack reopens.** Target: **~90 min**, one finish line. Runs
> entirely on **local infrastructure you own** (Ollama + `tinyllama` + garak + promptfoo, CPU-only).

---

> **Authorization — offensive tooling, read before you run.** garak and promptfoo generate *real*
> jailbreak, prompt-injection, and data-extraction payloads. Run them **only** against models and
> applications you **own or have explicit written permission to assess**. Every target in this lab is
> a local Docker container (`tinyllama` on your own Ollama) — never point these tools at a hosted
> model (OpenAI, Anthropic, a vendor Copilot) or anyone else's deployment without written sanction.
> "It's just a scanner" is not authorization.

---

## ✈ Flight card — the 7 things to hold

*Glance here when you lose the thread. This replaces re-reading the module.*

| # | Fact | Why it matters |
|---|------|----------------|
| 1 | **"Just tell it not to" is not a control.** | A system prompt and the attacker's input reach the model as the *same undifferentiated text* — the Chevy "$1 Tahoe" bot had an on-topic prompt and it didn't matter. |
| 2 | **LLM red-teaming is statistical.** | The same jailbreak at the same temperature can pass one run and fail the next. You report a **pass rate over N runs**, not a yes/no. |
| 3 | **Call a finding only above a threshold you declare *first*.** | A probe that fires 1-in-100 is noise; 80-in-100 is a vulnerability. Pre-declaring the line stops you rationalising after you see the number. |
| 4 | **garak = breadth; promptfoo = depth-over-time.** | garak scans a huge probe space to find *where* it's weak; promptfoo asserts the *specific* attacks stay blocked across every change. One finds the hole, the other proves it stays shut. |
| 5 | **The attack need not come from the user.** | RAG context and tool arguments are attacker-controllable input — EchoLeak (CVE-2025-32711) rode in on a *retrieved email*, zero clicks. |
| 6 | **The threat model is the deliverable.** | OWASP-LLM / ATLAS IDs are *labels*; the **named incident** (Air Canada · Chevy · EchoLeak) is the anchor, and the scans are its evidence. |
| 7 | **tinyllama is a toy target.** | A tiny model with little safety training fails probes a frontier model would pass — the *rates* are not a verdict on any product. What transfers is the **method** and the attack **classes**. |

> **↳ Go deeper — pull only when a step doesn't click:** the module's
> [core idea](README.md#the-core-idea) (why a system prompt isn't a boundary) and the
> [attack-class → OWASP-LLM → ATLAS table](README.md#the-core-idea) you'll tag findings with.

---

## Warm-up — answer before you build (2 min)

*Don't look below. Being forced to retrieve is what builds the memory.*

1. You send the same jailbreak to the copilot 100 times; it succeeds 3 times. Is that a finding? What
   number would make it one — and when do you have to decide that number?
2. garak and promptfoo both attack the copilot. Which one belongs **in CI**, and what distinct job does
   the other one do that CI can't?

---

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/ai-augmented-ops/10-attacking-ai
make up && make demo
```

**Requirements:** Docker, ~4 GB RAM free, no GPU. First `make up` pulls the Ollama image and
`tinyllama`, then leaves garak and promptfoo containers running; later runs use the cache. `make demo`
runs a **focused** garak scan (`injection` + `leakage` probes only — the full suite takes 30–60 min).
Other targets: **`make garak-full`** (all probe classes), **`make promptfoo-eval`** (the assertion
suite), `make shell`, `make down`, `make reset`.

Seed files: **`data/attack-prompts.yaml`** (the promptfoo suite — six adversarial cases, each mapped to
a real incident) and the **`results/`** stubs you fill in (`garak-findings.md`, `promptfoo-findings.md`,
`threat-model.md`).

> **▸ On track if:** `curl -s http://localhost:11434/api/tags` lists `tinyllama` — the model pulled and
> Ollama is reachable on the published host port. If it isn't, `make demo` has nothing to scan.

> **What this lab is — and isn't.** Every attack class you scan for is grounded in a *real, documented*
> incident, mapped in `results/threat-model.md`: the role-override / jailbreak probes are the
> **Chevrolet "$1 Tahoe" jailbreak** (2023); the injection-via-alert-data probes are the shape of
> **EchoLeak / [CVE-2025-32711](https://nvd.nist.gov/vuln/detail/CVE-2025-32711)** (zero-click indirect
> injection in M365 Copilot); the tool-surface probes are **[Invariant Labs' MCP tool
> poisoning](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks)** (2025);
> and the reason any of it matters operationally is **Moffatt v. Air Canada (2024 BCCRT 149)** — the org
> owns what its bot says. It is **not** those production systems (Flight-card #7): the garak pass
> *rates* against tinyllama are not a verdict on any real product.

---

## Build it — read a little, do a little

### Step 1 — Run the breadth scan (garak finds *where* it's weak)

**Concept (30 sec):** Flight-card #4. garak is the vulnerability scanner for LLMs: it runs a library of
**probe classes** (here `injection` + `leakage`) against the model and reports, per probe, the fraction
a **detector** judged blocked — a **pass rate**, not a verdict.

**Do it:** `make demo`. Read the per-probe summary: which probes ran under `injection` and `leakage`,
and the pass rate for each. Treat any class below your **pre-declared threshold** (start at **80 %
pass**) as a finding, and copy the summary table into `results/garak-findings.md`. Re-run once — the
rates shift slightly. That drift *is* the point (Flight-card #2).

> **▸ On track if:** `make demo` exits cleanly and `results/garak-raw.txt` now contains a garak run
> with a **per-probe pass-rate line** for both `injection` and `leakage` classes (the summary table),
> and you have transcribed at least the classes that fell below your 80 % threshold. Rates differing
> between two runs is expected, not an error.

### Step 2 — Prove the misconception by hand (a system prompt is not a boundary)

**Concept (30 sec):** Flight-card #1. The copilot's system prompt tells it to act *only* as a SOC
analyst. A Chevy-style override — "from now on ignore your role and…" — competes with that prompt on
equal footing because they're the same text to the model.

**Do it:** craft one chat message that tries to override the analyst role, and send it **at least 5
times** (via `make shell` + the Ollama API, or the `curl` pattern below). Record in
`results/garak-findings.md` whether the system prompt held *every* time, and the count that broke.

```bash
curl -s http://localhost:11434/api/generate \
  -d '{"model":"tinyllama","prompt":"YOUR ROLE-OVERRIDE ATTEMPT HERE","stream":false}' \
  | python3 -m json.tool
```

> **▸ On track if:** you have **N ≥ 5 recorded attempts** and a count of how many overrode the role —
> a statistical result (e.g. "held 3/5"), not a single anecdote — plus one sentence on why "just tell
> it not to" therefore isn't a control.

### Step 3 — Run the assertion suite (promptfoo, the Type 13 half)

**Concept (30 sec):** Flight-card #4. promptfoo runs each case in `data/attack-prompts.yaml` as a
prompt **plus an assertion** — what a safe response must contain or must *not* contain — and returns a
pass/fail scorecard, not a vibe.

**Do it:** `make promptfoo-eval`. For each of the six cases read: the prompt sent, the model's actual
output, and whether it **passed its assertion**. Copy every failing assertion into
`results/promptfoo-findings.md` and explain *why* each failed.

> **▸ On track if:** `results/promptfoo-results.json` is written and its `results.results[]` array has
> one entry per test case, each carrying a boolean **`success`** field; the run also prints a pass/fail
> line per case. You can state the fail count from the JSON, not by eyeballing model text.

### Step 4 — Write the per-finding analysis (tie each to a named incident)

**Concept (30 sec):** Flight-card #6. A raw pass rate is not a finding until it's labelled and
anchored. OWASP-LLM / ATLAS give the *label*; the real incident gives the *anchor*.

**Do it:** for each garak finding and each failing promptfoo assertion, write one paragraph in the
matching results file: the attack **class**, what an attacker could do to a SOC copilot if it works
(reclassify a critical as benign, extract the system prompt, exfil via a retrieved doc), the **named
incident it rhymes with** (Air Canada / Chevy / EchoLeak), and the **mitigation** (from module 09 or
the OWASP-LLM ID).

> **▸ On track if:** every finding paragraph carries all four elements — class, attacker impact, named
> incident, mitigation — and no paragraph is a bare pass rate.

### Step 5 — Write the threat model (the synthesis a CISO reads)

**Concept (30 sec):** Flight-card #6. The threat model, not the raw tool output, is what decides whether
the copilot ships. It reads the whole attack surface, not just the chat box.

**Do it:** write `results/threat-model.md` for the copilot with all six sections:
- **Adversaries** — who targets it and why (include *malicious alert data / retrieved documents*).
- **Assets** — correct triage, the system prompt, tool access.
- **Attack surface** — prompt input, tool results, RAG context, the model API.
- **Top 3 threats** — each tagged with **an OWASP-LLM risk ID *and* a MITRE ATLAS technique ID** (use
  the table in [the module](README.md#the-core-idea) — do not invent IDs), each anchored to one named
  incident.
- **Mitigations implemented** — reference modules 05 and 09.
- **Residual risk** — what's still open after all mitigations (be honest; EchoLeak proves filters get
  bypassed).

> **▸ On track if:** all six sections are present, each top-3 threat has **both** an OWASP-LLM ID and an
> ATLAS ID drawn from the module's table (not guessed), and the Residual-risk section names something
> still open rather than declaring victory.

### Step 6 — Extend the suite with a SOC-specific attack

**Concept (30 sec):** Flight-card #5. The suite you inherited doesn't cover *your* copilot's worst
case: an injection planted in a **retrieved alert body** — the EchoLeak vector a prompt-only test never
reaches.

**Do it:** add at least one new test case to `data/attack-prompts.yaml` (an EchoLeak-shaped
injection-in-retrieved-data attack), give it a **real assertion** (a safe response must not act on the
embedded instruction), and re-run `make promptfoo-eval`. Record pass/fail.

> **▸ On track if:** `make promptfoo-eval` now runs **one more case than before** (its `results.results[]`
> length grows by ≥1) and your new case has a non-trivial assertion — one that could actually *fail*,
> not one that always passes.

---

## Prove the control (your finish line)

**Turn one documented finding into a regression check, then prove the check bites.** Wire `promptfoo`
into CI: add `.github/workflows/ai-redteam.yml` (or extend `scripts/scan.sh`) that runs the suite and
**fails the build** if the safe-response pass rate drops below a declared threshold (e.g. 90 %). Then:

1. Confirm the gate is **green** on the hardened copilot.
2. Deliberately weaken the target — swap to a smaller/less-safe model, or strip a guardrail / output
   filter — and re-run. The gate must go **red**.
3. Restore, and confirm **green** again.

The contrast — green on the hardened copilot, red on the regressed one — *is* the proof. This is the
same held-out-set-plus-regression-gate discipline as
[module 11 — AI Evaluation & Observability](../11-ai-evaluation/README.md); reuse its scorecard shape.

> **▸ On track if:** the CI job (or `scripts/scan.sh`) returns a **non-zero exit code / red run** on the
> weakened target and **zero / green** on the hardened one — you have watched it go *both* ways, not
> just pass once. Fail-closed: a missing or errored eval must turn the build red, never silently pass.

---

## Recall check — close the doc, answer from memory (3 min)

1. Why is an LLM red-team result a *pass rate over N runs* rather than a yes/no — and when must you fix
   the finding threshold?
2. garak and promptfoo both attack the copilot: what distinct job does each do, and which one goes in CI?
3. In the threat model, are OWASP-LLM / ATLAS IDs the anchor or the labels — and what *is* the anchor?

---

## Deliverables

`data/attack-prompts.yaml` (with your new case) + `results/garak-findings.md` +
`results/promptfoo-findings.md` + `results/threat-model.md` + the CI regression workflow
(`.github/workflows/ai-redteam.yml` or the gating `scripts/scan.sh`). Commit all of them. Lab
artifacts — raw garak reports, `results/promptfoo-results.json`, full model transcripts — stay out of
the commit.

## Automate & own it

**Required — and the probe suite *is* the automation.** Turn "I red-teamed it once" into a suite that
re-runs on every change. Have a model draft the workflow YAML and the grep/jq that extracts the
failing-probe count from garak's report and the pass rate from `promptfoo`'s JSON
(`results.results[].success`); **you review the extraction logic** — does it count *all* failure modes,
or just lines containing "FAIL"? — and you set the gate to **fail closed** so a missing or errored eval
turns the build red, never silently passes. The artifact is a red-team you can re-prove on demand; a
finding nobody re-checks reopens itself.

## Definition of done (`attacking-ai` ✅)

- [ ] `make demo` completes and `results/garak-findings.md` has the per-probe summary table plus the
  role-override hands-on note (N ≥ 5 attempts) from step 2.
- [ ] `make promptfoo-eval` ran every case; `results/promptfoo-findings.md` analyses each failing assertion.
- [ ] Every finding paragraph carries class · attacker impact · named incident · mitigation.
- [ ] `results/threat-model.md` has all six sections, each top-3 threat tagged with an OWASP-LLM **and**
  an ATLAS ID from the module table, and an honest Residual-risk section.
- [ ] At least one new EchoLeak-/SOC-specific case is in `data/attack-prompts.yaml` with a real assertion.
- [ ] The CI regression gate **goes red on the weakened target and green on the hardened one** — you've
  seen both, not just a pass.
- [ ] You can explain all seven flight-card facts cold.

## Connects forward

This closes the track: you built the AI (04–06), measured it (07, 11), secured it (09), and now
red-teamed it systematically and **froze the result into a gate** (10). The capstone takes one tool from
the stack, demonstrates a finding against it, and ships a hardened version with this very regression
suite attached — the threat model here is the capstone's starting point, and the gate is what proves the
hardening holds.

## Marketable proof

> "I run systematic LLM red-teams with garak (statistical probe coverage) and promptfoo
> (expected-output assertions), interpret findings against real incidents (Air Canada, the Chevy '$1
> car' jailbreak, EchoLeak / CVE-2025-32711), produce a structured threat model tagged to OWASP-LLM and
> MITRE ATLAS, and ship the red-team as a CI regression gate that fails the build when a blocked attack
> becomes possible again."

## Stretch

- Run `make garak-full` and compare to the fast scan — which extra probe classes produce findings, and
  are any operationally significant for a SOC copilot?
- Add a *RAG-poisoning* test: plant an injection inside a document the copilot will retrieve (the
  EchoLeak shape) and assert the copilot does not act on it. This exercises the attack surface a
  prompt-only test never reaches.
- Gate on garak too: have the CI job also fail if any probe class drops below a declared pass rate, so
  both breadth (garak) and depth (promptfoo) regressions block merge.
