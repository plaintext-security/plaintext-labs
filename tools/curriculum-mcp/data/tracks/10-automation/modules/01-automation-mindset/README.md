# Module 01 — The Automation Mindset

*Variant D · concept autopsy, predict-then-reveal (+ an ADR deliverable). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Security Automation** — *automate the repeatable so humans can own the judgment — and learn why the gate is the point.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~3–4 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }


## Why this matters
This is the first module of the automation track, and it sets the posture for everything after it.
Before you write a line of Terraform, a CI gate, or a SOAR playbook, you need to answer two
questions: *what* should be automated, and *what has to be true* before you let an automation run
unattended. Get the first wrong and you burn out humans or hand judgment to a script. Get the second
wrong and you build a machine that does the wrong thing **faster than any human can stop it.** You'll
learn both by taking apart a 45-minute, $440-million automation disaster and naming exactly what was
missing.

## Objective
Decide, for a set of real security tasks, where the **automate / assist / leave-manual** cut line
falls — and *defend* that decision in an Architecture Decision Record (ADR). Along the way, explain
why automation increases speed in *both* directions, and what a "gate" actually is.

## The case
On **August 1, 2012**, the trading firm **Knight Capital** deployed new code to its order-routing
system across **eight production servers**. The deploy was done by hand, server by server, and on
**one** of the eight, the new code didn't get copied. That server kept running the old code.

Here's the part that turns a sloppy deploy into a catastrophe. The new code **reused an old feature
flag** — a flag that, years earlier, had switched on a piece of test logic called "Power Peg" that
was designed to buy high and sell low to exercise the system. The flag had been dormant and safe.
When the new deploy flipped that flag on, seven servers ran the new behavior — but the eighth, still
running the old code, interpreted the flag as "run Power Peg." At **9:30 a.m.**, the market opened.
That one server began firing millions of unintended orders into the market, buying high and selling
low, **as fast as the automation could send them.**

It ran for roughly **45 minutes** before anyone could stop it. In that time Knight executed millions
of trades, took on billions in unwanted positions, and ended the day **~$440 million** poorer — a
loss that effectively destroyed the company within days. The sequence is laid out in the
[SEC's order against Knight Capital (Exchange Act Release No. 70694, Oct. 2013)](https://www.sec.gov/litigation/admin/2013/34-70694.pdf).

## Call it before you read on
Don't scroll. Write down one answer — being wrong here is the entire point; it's what makes the
lesson stick.

> **Automation makes you safer, right? You replace error-prone humans doing the same thing over and
> over with a machine that does it the same way every time. So how does adding automation lead to the
> *fastest* corporate suicide in trading history?**

Most people reach for "the automation was buggy" or "they should have tested it more." Hold that
thought.

## The reveal — automation made them *faster*, including at being wrong

The Knight code wasn't doing something humans couldn't do — humans place orders too. What the
automation changed was **speed and scale**. A human trader who started buying high and selling low
would notice within a few trades, feel the loss, and stop. The automation felt nothing. It executed
the wrong action **millions of times in the window a human needs to read one alert.** That's the
whole lesson of this module, and it's the opposite of the comfortable intuition:

> **Automation does not make you safer. It makes you *faster* — and faster cuts both ways. It is a
> force multiplier on whatever you point it at, including your mistakes, executed at a scale and speed
> no human can catch in time.** The safety doesn't come from the automation; it comes from the
> **gate, the kill-switch, and the review** you wrap around it. Those are the point.

Three things Knight didn't have, and every one of them maps to a control you'll build later in this
track:

- **No gate.** The deploy had no automated check that all eight servers ran identical code before
  going live — a `plan`/diff step that *fails the rollout* on a mismatch. Module 03's IaC scanners and
  module 05's CI/CD pipeline are exactly this: a machine that refuses to proceed when the state is wrong.
- **No kill-switch.** When the orders started flooding out, there was no flag to flip, no one-command
  stop. Stopping it meant people scrambling to figure out *which* system and *how* — for 45 minutes.
  A safe automation can be paused in 60 seconds without a code change and a deploy.
- **No review of the dangerous detail.** Reusing a live, repurposed feature flag is the kind of thing
  a second pair of eyes catches. "AI authors → you review → you own it" is this same discipline applied
  to automation that a model writes for you (module 10).

If you want the same lesson with a different villain, look at the **AWS S3 outage of February 28,
2017**. An engineer running an established, *automated* runbook to debug a billing system **mistyped
one argument** to a command. The command was meant to remove a small number of servers; the typo
removed a much larger set, taking down a core S3 subsystem in **us-east-1** — and with it large
swaths of the internet that depended on it — for about four hours. AWS's own
[Summary of the Amazon S3 Service Disruption](https://aws.amazon.com/message/41926/)
is admirably honest: the runbook was automation that gave one human the reach to break a continent's
worth of infrastructure with one keystroke, faster than any safeguard could intervene. Their fix was
not "stop automating" — it was to add a **gate** (the tool now refuses to remove capacity below a
safe threshold). Same moral as Knight: the gate is the safety, not the automation.

### So what *do* you automate? (the judgment that's left)

The reveal isn't "automation is dangerous, do less of it." It's that **what you automate is a
judgment call**, and the criteria are concrete. Two axes decide it:

- **Repeatability** — does this *exact* sequence of steps happen more than a few times a month?
  Looking up an IP in three threat-intel feeds: yes. Deciding whether a breach is material enough to
  notify regulators: no, every instance is different.
- **Determinism** — given the same inputs, does the *correct* answer always look the same? "Decode
  this header and extract the sending IP" is deterministic. "Is this alert a real incident?" is not —
  it needs context a script doesn't have.

Cross them and you get three zones, and the middle one is where most security work actually lives:

| Zone | Looks like | What you do |
|------|-----------|-------------|
| **Automate** | high repeatability **+** high determinism | full automation — *with* logging, a gate, and a kill-switch |
| **Assist** (human-in-the-loop) | high repeatability **+** medium determinism | automate the data-gathering; a human makes the call |
| **Leave manual** | low repeatability **or** low determinism | don't automate; write a better runbook instead |

And there's an **ROI** test that gates whether even an "Automate" task is worth it:

> **ROI ≈ (minutes saved × times per week) − maintenance burden.**

The maintenance term is the one everybody skips. An automation that saves 30 minutes a week but
breaks — and needs 4 hours of fixing — every time an upstream API or output format changes is a *net
loss*. Maintenance is systematically underestimated for anything that calls external APIs, scrapes
web pages, or parses undocumented tool output, because those change without notice.

The posture the whole track builds toward: **AI authors → you review → scanners gate → you own it.**
The automation handles the mechanics; *you* understand every step and can defend every decision it
makes. "I don't know what that script does" is not an acceptable answer for a security tool running
in production — Knight is what that answer costs.

## Learn (~2 hrs)

*Short on purpose. The autopsy above is the spine; read these to deepen the mechanism, not to
relearn it.*

**The disasters, from primary and credible sources (~1 hr)**
- [SEC order against Knight Capital (Release No. 70694, Oct. 16 2013)](https://www.sec.gov/litigation/admin/2013/34-70694.pdf) — the regulator's own account: the eight-server deploy, the dormant "Power Peg" flag, the missing controls. Skim the "Summary" and "Facts" sections (~10 pages) — this is your evidence file for the lab's autopsy paragraph.
- [AWS — Summary of the Amazon S3 Service Disruption in us-east-1 (Feb 28 2017)](https://aws.amazon.com/message/41926/) — a model post-incident write-up (~5 min). Note what they changed: a *guardrail* on the runbook tool, not the removal of automation.

**Where automation pays off, and where it bites (~1 hr)**
- [Google SRE Book — "Eliminating Toil"](https://sre.google/sre-book/eliminating-toil/) — the SRE definition of *toil* (manual, repetitive, automatable, no enduring value) maps cleanly onto security ops. Read it for the criteria that decide what's worth automating. Free online.
- [Google SRE Workbook — "Eliminating Toil" (companion chapter)](https://sre.google/workbook/eliminating-toil/) — the practical follow-on: how to measure toil and decide what to attack first; read the "Identifying toil" and ROI-style sections for the maintenance-burden trap this module warns about. Free online.

## Key concepts
- Automation doesn't make you safer — it makes you *faster*, in both directions; safety is the **gate + kill-switch + review** wrapped around it
- The three missing controls behind Knight Capital: **no gate** (no check the rollout was consistent), **no kill-switch** (couldn't stop it in 60s), **no review** (a repurposed live flag slipped through)
- Repeatability + determinism decide the cut line: **Automate** / **Assist** (human-in-the-loop) / **Leave manual**
- ROI ≈ (time saved × frequency) − maintenance burden — the maintenance term is the one that's always skipped
- "AI authors → you review → scanners gate → you own it" — the track posture; *what* you automate is itself a judgment

## AI acceleration
This is the module where AI's job is *analysis*, not authoring. Hand a model your task list and the
two axes and ask it to sort each task into automate / assist / leave-manual with reasoning. It returns
a fast, confident first pass — and a good one to interrogate, because models tend to **over-rate
determinism** (calling "is this a real incident?" automatable because it *sounds* mechanical) and
**under-rate maintenance burden** (ignoring that the API it depends on changes monthly). Pick the two
placements you most disagree with and argue the other side; see whether its reasoning holds. The
first-pass sort is the model's; the **cut line is yours to defend** — which is exactly what the lab's
ADR makes you write down.
