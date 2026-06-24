# Module 19 — Reviewing AI-Generated Detections

*Type 14 · Adversarial Review — take a batch of AI-drafted Sigma rules, log parsers, and triage verdicts that are *subtly* wrong (matches the wrong field, drops a slice of lines, over-trusts a stale IOC, cites a hallucinated ATT&CK ID), find every planted error and prove it against the primary source, then codify when to trust AI detection output; you commit the corrected artifacts plus a review checklist. (Secondary: Eval Harness — you verify each fix by firing it against labelled data, not by re-reading it.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Defensive Operations** — *the AI writes the rule in seconds; the review is the job.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~4–5 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md), and [08 Detection-as-Code](../08-detection-as-code/README.md)
{ .module-meta }

!!! abstract "In 60 seconds"
    Every "AI acceleration" box in this track says *AI authors → you review → you own it*. This is the
    module where review **is** the lab. A model drafts a Sigma rule, a log parser, a triage verdict — all
    fluent, idiomatic, confidently correct-looking. Buried inside: a rule matching `Image` where it meant
    `ParentImage`, a parser whose regex silently drops 5% of lines, a verdict that closes a ticket because
    it over-trusts a year-stale IOC, an ATT&CK ID that doesn't exist. None of these are visible from a
    casual read; all are obvious from a systematic one. You'll find every planted error, prove each against
    the primary source, and write the trust policy that decides what you re-verify before any AI detection
    ships.

## Why this matters
AI will draft the detection. That is no longer the skill. A model produces a syntactically perfect
Sigma rule from a sentence, a VRL/regex parser from a sample line, and a tidy triage narrative from an
alert — in seconds, and they *look* right. The differentiating skill is catching the ones that are
subtly, dangerously wrong before they go live: the rule that compiles and runs but watches the wrong
field and so never fires; the parser that ingests "successfully" while dropping a slice of events into
the void; the triage verdict that confidently closes the one ticket that mattered. A detection programme
that ships AI output unreviewed isn't faster — it's faster at being silently blind. This module turns
the track's pervasive advisory ("you review it") into one concrete, scored exercise.

## Objective
Given a batch of AI-drafted detection artifacts (Sigma rules, a log parser, triage verdicts) seeded with
realistic, planted errors, find every one; for each, state the *tell* that gave it away and verify it
against the primary source; fix it and prove the fix against data; and codify a reusable trust checklist
for AI-generated detection output.

## The core idea

**AI's most dangerous property in detection is that the output is plausible.** The structure is
idiomatic, the YAML is valid, the regex parses, the triage narrative reads like a competent analyst
wrote it. That fluency is exactly what disarms review — you read it, it sounds right, you ship it. The
2025 study *Evaluating LLM Generated Detection Rules* makes the point concretely: an automated detection
engineer can produce rules that look human-authored, and the only way to know whether they're *good* is
to evaluate them against held-out ground truth, not to admire the YAML. Adversarial review is the
discipline of refusing the fluency and asking, every time: *is this actually true, and does it actually
fire?*

**The failure modes cluster, and that's what makes a checklist possible.** Across the detection domain
they fall into a small set you can hunt deliberately:

- **Wrong field, right shape.** The single most common detection bug — the rule matches `Image` where
  it should match `ParentImage`, or `CommandLine` where it should match `OriginalFileName`. It's valid,
  it converts cleanly, it runs every day, and it never fires. You catch it only by firing it.
- **Silent drops in a parser.** A regex or VRL that handles the sample line the model was shown but
  fails a real-world variant (a quoted field, a multiline message, a different timestamp), dropping a
  percentage of events with no error. The "successful" parse rate hides the gap.
- **Over-trusted / stale intelligence.** A triage verdict that closes (or escalates) a ticket because it
  treats an IOC as live when it's a year stale, or treats a single low-confidence indicator as proof —
  the misconception-reveal from module 15 (threat intel) showing up in AI clothing.
- **Hallucinated artifacts.** A confidently-cited ATT&CK technique ID that doesn't exist, a CVE that was
  never assigned, an event ID that's off by a digit. This isn't hypothetical: code-generating models
  invent non-existent software packages in roughly 1 in 5 outputs (the *package hallucination* research),
  and detection models hallucinate technique IDs and field names the same way. Every external identifier
  in AI output is a claim to verify, not a fact.

**The tell, the primary source, and the fire-test — every finding needs all three.** Catching the error
is not enough; the deliverable is *how you knew* and *how you proved it*. For each finding you name the
**tell** (the signal that made you suspicious — "this rule should fire on the malicious sample and
doesn't"), then **verify against the primary source** (the field against the actual event schema, the
ATT&CK ID against [attack.mitre.org](https://attack.mitre.org), the Sigma field against the
[Sigma specification](https://github.com/SigmaHQ/sigma-specification)), then **prove the fix** by firing
the corrected rule at labelled data — because a fix you only re-read is a fix you're trusting on the same
fluency that fooled you the first time. That triad — tell, source, fire — *is* the trust policy, and
writing it down so the next AI-drafted rule clears the same bar is the artifact this module produces.

!!! warning "The gotcha"
    "It runs without error" tells you nothing about a detection. A rule watching the wrong field, a parser
    silently dropping lines, and a triage verdict over-trusting a stale IOC all run perfectly. *Runs* and
    *correct* are different questions — only firing it against data where you know the answer settles the second.

## Learn (~2.5 hrs)

**The case for evaluating AI detections (~1 hr)**
- [Evaluating LLM Generated Detection Rules in Cybersecurity — Bertiger et al., CAMLIS 2025 (arXiv 2509.16749)](https://arxiv.org/abs/2509.16749) — the current primary source: an open framework that scores LLM-generated rules against a held-out set of human-authored detections, with metrics built to mirror how experts actually judge a rule. Read the intro + methodology; the takeaway is *measure against ground truth, don't admire the YAML*.
- [We Have a Package for You! — Spracklen et al. (arXiv 2406.10279)](https://arxiv.org/abs/2406.10279) — the package-hallucination study: 5.2% (commercial) to 21.7% (open-source) of LLM-suggested packages don't exist, 205k+ unique invented names. Read the abstract + findings; it's the hard evidence that *any* identifier an AI emits — package, CVE, ATT&CK ID — is an unverified claim.

**What the ground truth actually is (~1 hr)**
- [SigmaHQ/sigma-specification](https://github.com/SigmaHQ/sigma-specification) — the rule spec + the **modifiers appendix** (`contains`, `endswith`, `startswith`, `re`) and field-name conventions. This is what you check a drafted rule's *field and modifier* against. Skim the spec and the modifiers list.
- [SigmaHQ/sigma — published rules](https://github.com/SigmaHQ/sigma) — thousands of peer-reviewed rules; open `rules/windows/process_creation/` and read a few to internalise what field a correct rule *should* use (e.g. parent-child process logic). This is your reference for "wrong field, right shape."

**Verifying the claims (~30 min)**
- [MITRE ATT&CK](https://attack.mitre.org/) — the authority for technique IDs. Every ATT&CK tag in an AI-drafted rule gets checked here; a tag that resolves to nothing (or to a different technique) is a hallucination. Look up [T1059.001 (PowerShell)](https://attack.mitre.org/techniques/T1059/001/) to see what a real, resolvable ID looks like.

## Key concepts
- AI detection output is *plausible by construction* — fluency is what disarms review
- The detection failure-mode taxonomy: wrong-field, silent parser drops, stale/over-trusted intel, hallucinated identifiers
- "Runs without error" ≠ "correct" — the only proof is firing against labelled data
- Every external identifier (ATT&CK ID, CVE, field name) is a claim to verify against the primary source
- The review triad: the **tell** → the **primary source** → the **fire-test** — codified into a trust checklist
- A trust policy that says *what must always be re-verified* before AI detection output ships

## AI acceleration
The irony is the point: you use a model to *help* review the model. Ask one to critique an AI-drafted rule
and it will catch some issues and miss others — and invent a few that aren't there. So the move is the
three-way comparison: your manual findings vs. the model's vs. what actually happens when you fire the rule
at labelled data. Rate each source — what did the model catch that you missed, what did you catch that it
missed, what did *firing it* reveal that neither read found? That comparison is the empirical answer to the
question this whole module exists to settle: *when do I trust AI detection output, and what must I always
re-verify first?*

!!! question "Check yourself"
    - An AI-drafted Sigma rule converts cleanly and runs every day. What's the one test that tells you whether it's actually a detection?
    - A model cites `T1574.099` as the technique. What do you do before you tag the rule with it?
    - A parser reports a 100% successful parse rate. Why might 5% of your events still be missing?
    - Name the three things every review finding must carry, and why "I fixed it and re-read it" isn't enough.
