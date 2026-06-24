# Module 01 — The Hybrid AI Pattern

*Type 11 · Decision / ADR — the deliverable is a routing ADR (local model vs frontier vs human-in-the-loop) with the trade-offs made explicit and defensible. (Secondary: Misconception Reveal — model confidence ≠ accuracy.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**AI-Augmented Security Operations** — *not every task needs a frontier model; deciding what runs where is itself a security decision you have to defend.*

<!-- module-meta -->
**Type:** Decision / ADR (Family III) &nbsp;·&nbsp; **Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters

Security teams are under constant pressure to do more with less, and AI promises relief. But the
first real architectural decision in AI-augmented operations isn't *which model* — it's *what runs
where*. Reach for a hosted frontier model on every task and you create new problems: sensitive alert
data leaving the perimeter, unpredictable latency when a triage queue is growing, and a hard
dependency on a vendor API being reachable mid-incident. Push everything to a small local model and
you cap your reasoning ceiling on exactly the cases that need depth. The routing decision — local,
frontier, or human — is a security posture, and like any architecture decision worth making, it has
to be written down and defended. That's why this module's deliverable is an **Architecture Decision
Record (ADR)**: the artifact a practitioner produces *before* wiring AI into the SOC.

## Objective

Produce an **ADR** (Nygard format — Context · Options · Decision · Consequences) that routes a set
of representative security tasks across **local / frontier / human-in-the-loop**, scored against an
explicit constraint set, with honest consequences — including the attack-path and liability risk you
accept by choosing it.

## The core idea — call it before you read on

A support agent at a major airline answered a grieving customer's question about discounted
bereavement fares. It was fluent, specific, and confident: yes, it said, you can claim the
bereavement discount retroactively, within 90 days. The customer booked on that basis. The answer
was wrong — it contradicted the airline's own published policy — and the agent was a chatbot the
airline had deployed on its website.

> **Predict first.** The model was confident, fluent, and on-brand. It was answering a routine
> customer-service question, not a hard reasoning problem. *Wasn't it right?* And when it wasn't —
> who owns the wrong answer: the customer who trusted it, the vendor who built the model, or the
> company that deployed it? Write down your call before you read on.

### The reveal — confidence is not accuracy, and you own the output

In **Moffatt v. Air Canada (2024 BCCRT 149)**, the British Columbia Civil Resolution Tribunal
ordered the airline to pay damages for its chatbot's invented policy. Two findings make this the
anchor for the whole AI-augmented track:

1. **Confidence ≠ accuracy.** The bot wasn't hedging or visibly confused. It produced a confident,
   plausible, *specific* answer — a fabricated refund window — that happened to be false. Fluency is
   not a truth signal. A model that sounds certain about a CVE ID, an IOC, or a firewall rule is
   exhibiting exactly the same behaviour, with higher stakes.
2. **You own the output.** Air Canada argued the chatbot was "a separate legal entity responsible
   for its own actions." The tribunal rejected that outright: the company is responsible for *all*
   information on its site, whether it comes from a static page or a generative model. There is no
   "the AI said it, not us" defence. In a SOC, that means a hallucinated containment recommendation
   acted on is *your* incident, not the model's.

So the routing decision is not "which model is better." It's: **given that any model's output is a
confident draft you are accountable for, where does each task's blast radius let you put it?** Three
axes drive the call:

- **Sensitivity** — would you print this and hand it to a contractor? Internal hostnames, usernames,
  and PCI-in-scope data shouldn't leave the perimeter. *Moffatt* is the liability mirror of this:
  data residency is a compliance posture, not a latency preference.
- **Reasoning complexity** — a pattern-match on known signatures vs. cross-domain synthesis. A 7B
  local model is a fast first-tier analyst; a frontier model is a brilliant, expensive, rate-limited
  outside consultant.
- **Recoverability of a wrong answer** — the most important line in the table. Suggesting a search
  query is recoverable; triggering containment or pushing a firewall rule to prod is not. *Moffatt*
  is what an irrecoverable, unreviewed output costs.

Map the tasks against those axes and the routing falls out. Alert triage on internal logs —
high-sensitivity, recoverable, pattern-match — is **local**. A scrubbed post-incident executive
summary — medium-sensitivity, recoverable, high-complexity — earns **frontier**. Deciding whether
to pay a ransom — maximal stakes, irrecoverable — stays **human**, with the model preparing the
briefing, never making the call. The hard part isn't the routing logic; it's writing down *why*,
and being honest about what you accept when you're wrong.

This is a **Decision / ADR** module. There is no single right routing table — there's the one you
can defend. The deliverable is that defence.

## Learn (~3 hrs)

**The anchor — read the ruling and the analysis (~30 min)**
- [Moffatt v. Air Canada, 2024 BCCRT 149](https://www.canlii.org/en/bc/bccrt/doc/2024/2024bccrt149/2024bccrt149.html) — the actual decision (short, plain-language). Read paragraphs 24–28 on negligent misrepresentation and the rejected "separate legal entity" argument. This is the load-bearing primary source.
- [ABA Business Law Today — "BC Tribunal Confirms Companies Remain Liable for Information Provided by AI Chatbot" (Feb 2024)](https://www.americanbar.org/groups/business_law/resources/business-law-today/2024-february/bc-tribunal-confirms-companies-remain-liable-information-provided-ai-chatbot/) — a tight legal read of why deployment, not authorship, decides liability. The "you own the output" half of the reveal.

**Routing and risk framing (~1 hr)**
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) — LLM06 (Sensitive Information Disclosure) and LLM09 (Overreliance) are exactly the two risks the routing table manages. Read the descriptions and example scenarios; you'll cite at least one by ID in the ADR.
- [NIST AI Risk Management Framework — Govern function overview](https://airc.nist.gov/) — one page on what "govern" means for AI deployment. The MAP category is the mental model for writing the ADR's Context section.

**The ADR construct (~30 min)**
- [Michael Nygard, "Documenting Architecture Decisions" (2011)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) — the original ADR format. Short. Context / Decision / Consequences is the exact skeleton your deliverable uses; the discipline is honest Consequences.

**Practitioner view of local vs frontier (~1 hr)**
- [Simon Willison, "Things we learned about LLMs in 2024"](https://simonwillison.net/2024/Dec/31/llms-in-2024/) — dense, clear operational survey; read the sections on local models and on the gap between fluency and reliability. The empirical backdrop for the local-vs-frontier axis you'll score.

## Key concepts

- **Confidence ≠ accuracy** — fluent and specific is not the same as correct; *Moffatt* is the proof.
- **You own the output** — deployment, not authorship, decides accountability; no "the AI said it" defence.
- Three routing axes: **sensitivity · reasoning complexity · recoverability of a wrong answer**.
- Local (fast, private, lower ceiling) vs frontier (deeper, billed, every call leaves the boundary) vs human-only (irreversible/high-stakes).
- The ADR is the artifact: options scored against constraints, a defended decision, **honest** consequences.
- Data residency is a compliance posture, not just a latency choice.

## AI acceleration

Have a model draft the ADR scaffold and pre-populate the options/scoring table — it knows the
local-vs-frontier landscape well. **Your critical review is the Consequences section.** A model will
list mostly upside; explicitly ask it to populate the *negative* consequences and the attack-path /
liability note for your chosen routing, then verify each against the actual constraint set. A model
that tells you frontier-for-everything has no data-residency downside is doing the exact thing
*Moffatt* punishes: sounding confident about something it doesn't own. You own this policy — draft
with the model, defend it yourself.
