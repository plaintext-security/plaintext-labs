# Lab 16 — Reviewing AI Incident Summaries: Catch the Fabrications, Codify the Trust Policy

*Hands-on lab · [← Back to the module concept](README.md)*

> **Lab environment status:** the Docker environment for this lab is **to be built and validated**.
> The directory `plaintext-labs/forensics/16-reviewing-ai-summaries/` (a `docker-compose.yml`, a
> bundled `data/` set holding the seeded AI summary plus the primary artifacts it claims to describe,
> a `scripts/` verifier, and a `Makefile` with `up`/`down`/`reset`/`demo`) is not yet committed. The
> instructions below define the target shape; the lab is not "done" until `make up && make demo &&
> make down` is green on a clean Linux runner and this note is removed.

## Setup

```bash
git clone https://github.com/plaintext-security/plaintext-labs
cd plaintext-labs/forensics/16-reviewing-ai-summaries
make up && make demo
```

**Requirements:** Docker. ~256 MB RAM. **No network, no live model** — the lab ships a *recorded*
AI-generated summary (a committed fixture) and the primary artifacts it claims to describe, so the
review is deterministic and runs offline, in CI too. Python stdlib for the verifier; the artifacts
are small bundled logs, an EVTX-style event extract, a CloudTrail JSON slice, and a PE feature record
carried over from the Meridian case.

`make demo` runs a small **claim-verifier** that walks the summary's structured fields — every CVE,
every ATT&CK ID, every hash, every cited timestamp — and prints which trace to a bundled artifact and
which do not, then prints the count of planted fabrications it expects you to find by hand (the verifier
catches the mechanical ones; the *root-cause* error is yours to catch). The list of unsupported claims is
the spine of the lesson.

## Scenario

The Meridian investigation is wrapping up. A teammate, short on time, fed the merged timeline and
artifacts to a model and produced `data/ai-incident-summary.md` — a polished report with a timeline, an
IOC table, ATT&CK mappings, and a root-cause conclusion. It is going into the official incident report
**with your name on the review line**. Before you sign it, you must verify it. The summary contains
several realistic but false claims: at least one hallucinated specific (a CVE / a timestamp / an artifact
that isn't in evidence), at least one plausible-but-wrong structured field (an ATT&CK ID under the wrong
tactic, or a malformed hash), and a confidently-stated root cause that the artifacts contradict. Your job
is to find every one, prove it against the primary source, and write the trust policy that prevents the
next one.

> This uses a fictional scenario and recorded fixtures. No external targets, no live model, no
> authorization needed. The "AI summary" is a committed artifact, not generated at runtime.

## Do

1. [ ] **Predict before you read the artifacts.** Read `data/ai-incident-summary.md` once, as a reviewer
   would skim it. Write down, before checking anything, how many claims you *expect* are unsupported and
   which fields you trust least. (You'll compare this to what you actually find — fluency tends to inflate
   the prediction toward "looks solid.")

2. [ ] **Verify every structured field first — it's where fluency outruns grounding and the check is
   cheapest.** For each CVE in the summary, search [NVD](https://nvd.nist.gov/vuln/search) and confirm it
   exists *and* its affected products match the Meridian environment. For each ATT&CK `T####`, open the
   [MITRE technique page](https://attack.mitre.org/techniques/enterprise/) and confirm both the ID *and the
   tactic* match the behaviour the artifact shows. For each hash, recompute it against the bundled artifact.
   Record every mismatch with the *tell* that exposed it.

3. [ ] **Trace every timeline entry to a log line.** For each event in the summary's timeline, find the
   supporting line in the bundled artifacts (`auth.log`, the EVTX extract, the CloudTrail slice). Flag any
   entry that has **no artifact behind it** — the hallucinated-specific failure mode. State, for each, what
   you searched and why its absence is conclusive.

4. [ ] **Test the root cause against the evidence, not against its own coherence.** The summary states a
   confident root cause. Build the causal chain it implies and check each link against the timeline. Find
   where the evidence contradicts the story (e.g., a valid credential used from a new location vs. the
   summary's "brute force," or an artifact that predates the claimed initial-access vector). Write the
   corrected, *artifact-supported* root cause — and note explicitly where the true root cause is **unknown**
   from the available evidence, because "unknown" is a legitimate finding the model refused to give.

5. [ ] **Run the claim-verifier and reconcile.** `make verify` runs the bundled verifier over the summary's
   structured fields. Compare its output to your manual findings: confirm it caught the mechanical errors,
   and note the one(s) it *missed* (the root-cause error a field-checker can't catch) — that gap is the lesson
   on why automated verification assists review but does not replace it.

6. [ ] **Write the trust policy / review checklist.** Codify what you must *always* re-verify before AI-drafted
   forensic text ships, and the explicit boundary: what the AI is **allowed** to do (draft structure, summarise
   *verified* findings) versus what it must **never** do (assert a finding, supply a root cause, invent an
   artifact). Make it concrete enough that a teammate could apply it identically to the next summary.

## Success criteria — you're done when

- [ ] Every planted fabrication is found: each hallucinated specific, each wrong structured field, and the contradicted root cause.
- [ ] For each, you've recorded the **tell** and the **primary source** that proves it false (NVD record absent, ATT&CK tactic mismatch, recomputed hash, missing log line, contradicting timeline entry).
- [ ] The corrected root cause is artifact-supported, and you've named where the evidence leaves it **unknown**.
- [ ] You've identified at least one error the automated verifier could *not* catch and can explain why.
- [ ] The trust policy/checklist is written and includes the explicit allowed-vs-never boundary for AI-drafted forensic output.

## Deliverables

Commit to your portfolio repo:
- `review-findings.md` — the table of every false claim, its tell, and the primary source that disproves it; plus the corrected, artifact-supported root cause.
- `ai-trust-policy.md` — the reusable review checklist and the allowed-vs-never boundary.

Do **not** commit the AI summary fixture or the bundled artifacts (they're the lab's, gitignored); your findings
and policy are the artifacts.

## Automate & own it

**Required.** Turn the manual structured-field check into a reusable `summary_verifier.py` that, given an AI summary
and the artifact set, extracts every CVE / ATT&CK ID / hash / timestamp and reports which trace to an artifact and
which do not. Have a model draft it — it's read→extract→cross-reference boilerplate. **You own three things it will
get wrong:** (1) it must **fail loud, not silent** — an unrecognised or unparseable claim is flagged for human review,
never quietly passed; (2) it verifies *structure and presence*, and must explicitly **not** claim to validate the
root cause or any causal narrative (state that limit in its `--help` and output, because the limit *is* the lesson);
(3) a CVE/ATT&CK ID that is *well-formed but nonexistent* must be flagged — format-valid is not evidence-valid. Commit
`summary_verifier.py` alongside the findings.

## AI acceleration

Use a model as a **second reviewer**: paste the summary and the artifacts and ask "which claims here are not supported
by the attached evidence?" Then do the thing the module is about — **verify its answer**, because it will miss its own
class of error and may confidently bless a fabrication. Treat its output as leads checked against NVD and MITRE, never
a verdict. To build *more* practice material, ask a model to "rewrite this verified summary with three new realistic
false claims, and tell me separately which ones" — that's the Module 15 held-out-set discipline applied to review, and
it lets you test your checklist against fabrications you didn't plant yourself.

## Connects forward

This is the operational form of every prior module's "the AI output is a lead, not evidence" note, and it closes the
track: Module 14 taught the report structure and its completeness gate; this module is the *content* gate that runs
before it — no claim ships unless it traces to an artifact. The trust policy you write here is reusable on every
AI-drafted artifact you produce in later tracks.

## Marketable proof

> "I review AI-generated incident summaries adversarially — tracing every CVE, ATT&CK mapping, hash, and timeline
> entry to a primary artifact, catching hallucinated specifics and contradicted root causes, and I maintain a trust
> policy that defines what AI may draft versus never assert in a forensic report that carries my name."

## Stretch

- Extend `summary_verifier.py` to emit a **per-claim confidence/coverage scorecard** (claims-traced vs. claims-total)
  and gate a report at, say, 100% traceability for findings — connecting this module directly to the Module 14 report
  linter and the Module 15 eval gate.
- Write a one-page comparison of *your* corrected root cause against a published post-mortem of a real disclosed
  incident (e.g., a CISA or DFIR Report write-up), and note where a real investigation also had to say "unknown."
