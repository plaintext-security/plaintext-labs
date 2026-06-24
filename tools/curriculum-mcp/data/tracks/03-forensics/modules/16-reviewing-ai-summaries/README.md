# Module 16 — Reviewing AI Incident Summaries

*Type 14 · Adversarial Review — take a polished, confident, AI-generated incident summary seeded with fabricated events and a wrong root cause, catch every unsupported claim by tracing it back to a primary artifact, and codify a trust policy for AI-drafted forensic output; the deliverable is your review findings plus the checklist, not a rewrite. (Secondary: Misconception Reveal — "the summary reads right, so it is right" is the load-bearing error.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Digital Forensics & IR** — *an AI summary is a lead, never evidence — every conclusion in a forensic report must trace to an artifact, or it doesn't ship.*

<!-- module-meta -->
**Difficulty:** Advanced &nbsp;·&nbsp; **Estimated time:** ~3.5–5 hrs (study + lab) &nbsp;·&nbsp; **Type:** Adversarial Review &nbsp;·&nbsp; **Prerequisites:** [13 — Incident Response Process](../13-ir-process/README.md), [14 — Reporting & Root-Cause Analysis](../14-reporting-root-cause/README.md)
{ .module-meta }

## Why this matters

Every prior module in this track ends with the same advisory note: feed your timeline to a model, but the
output is a *lead*, not evidence — verify it against the artifact. This module is where that advice stops being
a footnote and becomes the work. You will be handed a forensic incident summary that an AI wrote: fluent,
structured, confident, complete with a timeline, an IOC table, MITRE ATT&CK mappings, and a root-cause
conclusion. It reads like the report a senior analyst would write. And it contains fabricated events that never
appear in the evidence, a CVE that doesn't exist, an ATT&CK technique mapped to the wrong tactic, and a root
cause that the artifacts actively contradict. None of that is visible from a careful *read* — fluency is not
accuracy, and a confident summary is the most dangerous kind of wrong, because it short-circuits the scrutiny
you would apply to a hesitant one. The skill that separates an analyst who can use AI from one who gets burned
by it is not prompting; it is rigorous, artifact-anchored review. This is not hypothetical: a New York lawyer
was sanctioned in 2023 after filing a brief full of ChatGPT-fabricated case citations he never verified, and
research finds general-purpose models hallucinate on the majority of specific legal queries — the forensic
report, headed for a regulator or a courtroom, has the same failure mode and higher stakes.

## Objective

Given a plausible, confident, AI-generated incident summary seeded with several realistic but false claims,
find every fabrication by tracing each claim to (or failing to find it in) the primary artifacts, document the
*tell* that exposed each one, and codify a reusable **trust policy / review checklist** for AI-drafted forensic
output.

## The core idea

> **This AI-written incident summary looks like a finished report — timeline, IOCs, ATT&CK IDs, a clean root
> cause. Is it right?** Before reading on, commit to a prediction: how many of its claims do you think you could
> *trace to an artifact*, and how many are the model filling a plausible gap?

The reveal: it is wrong in several specific, load-bearing ways, and **the reasons it's wrong are not random — they
are the characteristic failure modes of a language model asked to narrate forensic evidence.** Naming those failure
modes is the heart of this module, because once you know the shapes, you know where to look.

**Hallucinated specifics.** A model abhors a gap. Asked for a root cause when the evidence is ambiguous, it will
not say "unknown" — it will invent the most *plausible* answer: a CVE ID that fits the software version (but
doesn't exist or doesn't apply), a precise exploitation timestamp the logs never recorded, a phishing email no one
collected. The tell is always the same: the claim is stated with the same confidence as the well-supported ones,
but **there is no artifact behind it.** Your defense is not skepticism-by-feel; it is a rule — *every claim cites
its artifact, or it is a hypothesis, not a finding.*

**Plausible-but-wrong structured fields.** Models are fluent in the *format* of forensic output and routinely wrong
in the *content*. An ATT&CK technique will be cited with a correct-looking `T####` ID mapped under the wrong tactic,
or a technique that sounds right for the behaviour but isn't what the artifact shows. A hash will be the right length
and wrong value. These pass a skim precisely because the *shape* is perfect; they fail the instant you check the ID
against the actual ATT&CK page or recompute the hash. Structured fields are where the model's fluency most outruns
its grounding, and where verification is cheapest — so check them first.

**The wrong root cause stated confidently.** The most dangerous error is the narrative one: a causal story that
connects the events smoothly and is contradicted by the evidence — attributing the breach to a brute-force login
when the auth logs show a valid credential used from a new location (credential theft, not brute force), or naming
an "initial access via RDP" when the first malicious artifact predates any RDP session. A smooth story is seductive
and a model is built to produce smooth stories; the discipline is to test the *causal chain* against the timeline,
not to enjoy its coherence.

**The trust policy is the deliverable, not the corrected report.** Catching the planted errors once is an exercise;
the transferable output is the **checklist** — the standing list of what you *always* re-verify before AI-drafted
forensic text reaches a report: every CVE against NVD, every ATT&CK ID against MITRE, every hash recomputed, every
timeline entry traced to a log line, every causal claim tested against the evidence, and an explicit rule for what
the AI is *allowed* to do (draft structure, summarise verified findings) versus *never* do (assert a finding, supply
a root cause, invent an artifact). This is the operational form of the track's standing posture — **AI authors → you
review → you own it** — and it is what makes the difference between a tool that accelerates you and one that signs
your name to a fabrication.

## Learn (~2 hrs)

**Why confident AI output is the dangerous kind (~45 min)**
- [OWASP Top 10 for LLM Applications — LLM09 (Overreliance)](https://owasp.org/www-project-top-10-for-large-language-model-applications/) — the exact threat this module trains against: "failing to critically assess LLM outputs can lead to compromised decision making… and legal liabilities." Read the LLM09 description and its mitigations.
- [Stanford HAI — "Hallucinating Law: Legal Mistakes with LLMs Are Pervasive"](https://hai.stanford.edu/news/hallucinating-law-legal-mistakes-large-language-models-are-pervasive) — the research result that grounds the predict-then-reveal: models hallucinated on 69–88% of specific legal queries and were *overconfident regardless of accuracy*. The forensic report has the same failure mode and a courtroom audience.
- [Wikipedia — "Mata v. Avianca, Inc."](https://en.wikipedia.org/wiki/Mata_v._Avianca,_Inc.) — the 2023 case where a lawyer filed ChatGPT-fabricated citations and was sanctioned; the cautionary anchor for "fluent ≠ verified." Read the facts and the sanction.

**The verification primary sources (~45 min)**
- [NVD — National Vulnerability Database](https://nvd.nist.gov/vuln/search) — where you confirm (or refute) any CVE the summary cites; a CVE that returns no record, or whose affected products don't match, is a fabrication. The authoritative check for the "hallucinated CVE" failure mode.
- [MITRE ATT&CK — Techniques](https://attack.mitre.org/techniques/enterprise/) — where you verify every `T####` ID *and the tactic it sits under*; the common AI error is a real ID under the wrong tactic. Open the cited technique and confirm it matches the behaviour the artifact shows.
- [MITRE ATT&CK — T1070.006 (Timestomp)](https://attack.mitre.org/techniques/T1070/006/) — a worked example of a technique page: read how the technique, tactic, and detection are stated, so you know what "matches the artifact" looks like when you check the summary's mappings.

**Codifying review as a gate (~30 min)**
- [Anthropic — "Define success criteria and build evaluations"](https://platform.claude.com/docs/en/docs/test-and-evaluate/develop-tests) — how to turn "review it carefully" into measurable, repeatable criteria; the framing for writing a checklist a teammate could apply identically. Read the success-criteria section.

## Key concepts
- Fluent ≠ accurate: a confident summary short-circuits scrutiny, which makes it the most dangerous kind of wrong.
- The three AI failure modes for forensic narration: hallucinated specifics (CVEs, timestamps, artifacts), plausible-but-wrong structured fields (ATT&CK IDs under the wrong tactic, malformed hashes), and a smooth-but-contradicted root cause.
- The one rule that catches most of it: every claim traces to a primary artifact, or it's a hypothesis, not a finding.
- Verify structured fields first — fluency most outruns grounding there, and the check (NVD, MITRE, recompute the hash) is cheapest.
- Test the causal chain against the timeline; don't reward a coherent story for being coherent.
- The deliverable is the trust policy/checklist, not the corrected report — what the AI may draft vs. never assert.
- This is the operational form of "AI authors → you review → you own it."

## AI acceleration

The irony of this module is deliberate: you use AI to *help review* AI. A model is genuinely useful as a
**second reviewer** — paste the summary and the artifacts and ask "which claims in this summary are not supported
by the attached evidence?" — but it will miss its own class of error and confidently bless some fabrications, so
its findings are leads you verify against NVD and MITRE, never a pass/fail. Better: use a model to *generate the
adversarial training material* — "rewrite this verified summary with three realistic but false claims and tell me,
separately, which ones" — to build your own practice corpus, which is exactly the held-out-set discipline from
Module 15 applied to review. The judgment that stays yours: every CVE checked against the primary source, every
ATT&CK ID against MITRE, every causal claim against the timeline — and the explicit decision about what the AI is
permitted to assert in a report that carries your name.
