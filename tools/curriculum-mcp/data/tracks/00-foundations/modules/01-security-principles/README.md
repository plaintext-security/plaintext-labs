# Module 01 — Security First Principles

*Variant D · concept autopsy, predict-then-reveal. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Foundations** — *the vocabulary and mental models the whole field is built on — learned by taking one famous breach apart.*

<!-- module-meta -->
**Difficulty:** Beginner &nbsp;·&nbsp; **Estimated time:** ~3–4 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** None — start here
{ .module-meta }


## Why this matters
Before any tool, before any track, you need the shared language: what security is actually trying to
protect, who is allowed to do what, and the handful of principles every later decision traces back to.
This module teaches that language by using it — you'll take apart **Equifax 2017**, one of the most
expensive breaches in history, and name exactly which principle gave way at each step. That muscle —
"see a system, see all the ways it fails" — is the lens you carry into all twelve tracks.

## Objective
Explain the core security models — the CIA triad, AAA, defense in depth, least privilege — and use
them as **lenses** to dissect a real breach into the specific principle that failed at each step.

## The case
In 2017, **Equifax** — a company whose entire business is holding the most sensitive financial data on
nearly every American adult — lost **147 million people's records**: names, Social Security numbers,
birth dates, addresses. They were not a startup that forgot to buy security. They had firewalls. They
had encryption. They had a security team. And the data still walked out the door.

The chain, laid out in the [US GAO report](https://www.gao.gov/products/gao-18-559) and the
[House Oversight Committee report](https://oversight.house.gov/wp-content/uploads/2018/12/Equifax-Report.pdf),
was roughly this:

1. A public web app ran **Apache Struts** with a known, *already-patched* hole — **CVE-2017-5638**. A
   fix had shipped in March; Equifax hadn't applied it. Attackers used it to run commands on the server.
2. From that one server, attackers moved freely across the **internal network** and reached dozens of
   databases — because the internal network was **flat** (few internal walls).
3. A device that inspected outbound traffic had an **expired certificate**. It had been blind for
   **~76 days**. So the slow trickle of data leaving the network was invisible — until someone renewed
   the cert and the alarms finally fired.

## Call it before you read on
Don't scroll. Write down one answer — being wrong here is the entire point; it's what makes the lesson
stick.

> **Equifax had firewalls, encryption, and a security team. With all of that in place, how did 147
> million records walk out — what was the *one thing* that failed?**

Most beginners (and most headlines) name a single villain: "they didn't patch." Hold that thought.

## The reveal — there was no one thing

There was no single point of failure, because **security is not a single thing.** It is a property of
the *whole system*, and Equifax lost it the way systems always do: **a chain of separate principles
failed in series, and each one was supposed to catch what the last one missed.** The first principles
below aren't vocabulary to memorize — they're the **lenses** that let you see every link in that chain.

**The CIA triad — *what* you're protecting.** Three properties: **Confidentiality** (only the right
people can read it), **Integrity** (it can't be secretly altered), **Availability** (you can use it
when you need it). Nearly every attack and defense maps to attacking or protecting one of these.
Equifax lost **confidentiality** — 147M records read by people who shouldn't see them. But notice the
sneaky one: the expired cert took away the **availability of *detection*.** The monitoring couldn't be
*used*, so the breach ran for 76 days unseen. Availability isn't only about your website staying up;
it's about your *defenses* staying up too.

**Defense in depth — never trust one wall.** Layer your controls so that one failure isn't fatal. The
Struts hole was the *entry*, but an entry doesn't have to mean total loss — **if** there are inner
walls. Equifax's network was **flat**: get into one server, reach everything. That's a single perimeter
with nothing behind it. Defense in depth is the principle that was missing, and it's why one unpatched
app became 147M records instead of one compromised box.

**AAA and least privilege — *who* may do *what*.** AAA is **Authentication** (who are you),
**Authorization** (what are you allowed to do), and **Accounting** (what did you actually do —
the logging). A close cousin, **least privilege**, says: give every user, server, and process the
*minimum* access it needs, so a compromise stays *contained*. The web server that got popped could
reach databases it had no business touching — an authorization-and-segmentation failure. And the
**Accounting** that should have screamed "data is leaving" was the very thing the expired cert blinded.

**The model to keep:** *security is a property of the whole system, not a product you buy.* You can own
a firewall, encryption, and a security team and still lose everything — because the firewall, the
patching, the segmentation, and the monitoring are *different walls*, and an attacker only needs the
walls to fail **in a line.** First principles are how you check every wall before an attacker does. If
you answered "they didn't patch," you named the first domino — and missed the three behind it that
turned a routine vulnerability into a generational breach. That gap is exactly what this module closes.

## Learn (~2 hrs)

*Short on purpose. The autopsy above is the spine; read these to deepen the mechanism, not to relearn
the model.*

**The principles**
- [Professor Messer — The CIA Triad (Security+ SY0-701, ~8 min)](https://www.youtube.com/watch?v=SBcDGb9l6yo) — a crisp, free explainer of the core triad; follow it into his adjacent 1.2 videos on AAA and security controls. Watch for how every example maps back to one of the three properties.
- [NIST SP 800-12 Rev. 1 — An Introduction to Information Security](https://csrc.nist.gov/pubs/sp/800/12/r1/final) — the authoritative grounding. Skim **chapters 1–3** only (what security is, threats, and the control families); it's a reference, not a read-cover-to-cover.

**The breach, from the primary source**
- [US GAO — Actions Taken by Equifax and Federal Agencies in Response to the 2017 Breach (GAO-18-559)](https://www.gao.gov/products/gao-18-559) (~30 min, skim the "How the breach occurred" section) — the government's own timeline: the unpatched Struts flaw, the flat network, and the expired certificate. This is your evidence file for the lab.

## Key concepts
- The CIA triad — Confidentiality, Integrity, Availability (and detection is an *availability* concern too)
- AAA — Authentication, Authorization, Accounting (logging is part of security)
- Defense in depth — layer controls so one failure isn't fatal; a flat network is one wall with nothing behind it
- Least privilege — give every user/server/process the minimum access it needs, so a compromise stays contained
- Security is a property of the *whole system* — breaches are usually a chain of principles failing in series, not one villain

## AI acceleration
Hand a model the public Equifax timeline and ask it to map each failure to a security principle *before*
you write yours. It produces a fast, confident draft — and a good one to check, because models tend to
collapse the story into the single headline cause ("they failed to patch") and miss the quieter
failures: the flat network (defense in depth) and especially the **expired cert that blinded detection**
(an availability-of-monitoring failure most write-ups skip). Your job is to catch what it flattened. If
you can explain *why* the breach needed all three failures, not just the patch, you've learned the
module — and you own the verdict.
