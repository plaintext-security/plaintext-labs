# Module 12 — Threat Modeling

*Variant D · concept autopsy, predict-then-reveal. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Foundations** — *the last skill before the capstone: find the bugs on the whiteboard, before you touch a tool.*

<!-- module-meta -->
**Difficulty:** Beginner &nbsp;·&nbsp; **Estimated time:** ~4–5 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** Earlier Foundations modules (you'll model the lab system you built)
{ .module-meta }


## The case

In late 2013, attackers walked out of **Target** with the payment-card data of roughly **40 million
customers** — card numbers swiped at the checkout lanes during the holiday season. The how, laid out
in the [US Senate Commerce Committee "Kill Chain" report](https://www.commerce.senate.gov/services/files/24d3c229-4f2f-405d-b8db-a3a67f183883),
is the part worth sitting with:

1. The attackers did **not** start at Target. They stole the network login of **Fazio Mechanical**, a
   heating-and-refrigeration contractor — a small vendor with remote access to Target's systems for
   billing and project management.
2. With the vendor's credentials they reached **Target's internal network** — and once inside, the
   network was **flat**: little stopped them moving from the vendor-facing systems toward the systems
   that ran the stores.
3. They reached the **point-of-sale (POS) terminals** — the cash registers — and installed malware
   that scraped card numbers out of memory as cards were swiped.
4. The stolen data was **collected inside Target's own network**, then sent out to servers the
   attackers controlled.

Here is the uncomfortable part. Target was **PCI-compliant** — it had passed the payment-industry's
security audit. It had **firewalls.** It had **antivirus.** A monitoring tool even fired alerts that
were not acted on. By every box-checking measure, this was a secured company. So the question this
module turns on:

> **Target had firewalls, antivirus, and a passing compliance audit. Where was the trust boundary
> nobody guarded?**

## Your job

By the end of this module you'll do what a security engineer does *before* anyone writes code or runs
a scan: take a system, **draw the lines that data crosses**, and at each line ask, methodically, what
could go wrong. You'll do it on a system you already understand — the small lab you stood up earlier in
this track — and produce a **one-page threat model**: the data flow, the trust boundaries, and a
STRIDE pass that names a concrete threat and a mitigation at each crossing. The deliverable is the
artifact; the muscle is asking the question first.

## Call it before you read on

Don't scroll to the answer. Write down your gut response — being wrong here is the point.

> **Target spent heavily on security and passed its compliance audit. The attackers still got in
> through an HVAC vendor's login. What did all that firewall-and-antivirus spending fail to account
> for — what kind of threat does a checklist miss?**

## The reveal

A **trust boundary** is any place where data or a request moves from something *less trusted* to
something *more trusted* — from the internet to your web server, from a normal user to an admin
function, from a third party's network to yours. It's the moment something crosses a line and gets
treated as more legitimate than it was a second before. **Most security bugs live exactly on these
crossings**, because that's where someone decided "this side is safe" and stopped checking.

Target's spending defended the boundaries it had drawn: the internet versus its perimeter (firewalls),
files versus the host (antivirus), the audit's checklist of controls. But there was a boundary it had
on paper and never treated as one: **the vendor connection.** Fazio Mechanical sat *outside* Target,
yet its credentials opened a door *inside* — a less-trusted network reaching a more-trusted one. Nobody
guarded that crossing: the vendor's access wasn't tightly scoped, and once through it, the flat internal
network let the attackers walk from "vendor billing" all the way to the cash registers. The boundary
existed; it just wasn't *watched* or *segmented*.

This is why a compliance checklist misses it. A checklist asks "do you have a firewall?" — yes. It
doesn't ask "draw every place data crosses from less-trusted to more-trusted, and prove you defend each
one." That second question is **threat modeling**, and a threat-modeling pass would have put a bright
mark on `vendor network → internal network` as a crossing to defend: scope the vendor's access to only
what billing needs, segment the network so a vendor foothold can't reach the POS, and watch that
boundary. The cheapest place to catch this was a whiteboard in 2012, not a forensics report in 2014.

## The method: draw the boundaries, then STRIDE each one

Threat modeling is four questions asked in order: **what are we building, what can go wrong, what are
we doing about it, did we do a good job?** The first question is a *diagram* — the elements (browser,
server, database), the flows between them, and the trust boundaries those flows cross. The second
question is where it gets systematic instead of vibes, and that's what **STRIDE** is for. STRIDE is a
checklist of the six things that can go wrong at a boundary — walk each crossing and ask one question
per letter:

- **S — Spoofing:** can an attacker pretend to be someone (or something) they're not? *(The Target
  vendor login is spoofing: the attacker was "Fazio Mechanical" as far as the network knew.)* Defends
  authentication.
- **T — Tampering:** can they modify data or code they shouldn't — in transit or at rest? Defends integrity.
- **R — Repudiation:** can someone do something and then deny it, because nothing logged it? Defends accountability.
- **I — Information disclosure:** can they read data they shouldn't — the card numbers, the config file, the keys? Defends confidentiality.
- **D — Denial of service:** can they take the system down or make it unusable for everyone else? Defends availability.
- **E — Elevation of privilege:** can a low-privilege foothold turn into a high-privilege one — *exactly the flat-network pivot from vendor access to the POS?* Defends authorization.

Notice STRIDE maps straight back to the first principles from Module 01: spoofing↔authentication,
tampering↔integrity, information disclosure↔confidentiality, elevation↔authorization. The principles
and the method are the same idea — one stated, one applied.

The judgment to carry: **model the system before you touch a tool.** A scanner finds the bug that
already shipped; a threat model finds the one still on the whiteboard, which is the cheapest one there
is to fix. And when you use AI to help (you will), a model is a fast brainstorming partner for the
STRIDE pass — but the skill is **pruning**: cut the irrelevant, add the threats specific to *your*
system that a model can't know, and own the final page.

## Learn (~2.5 hrs)

*Deliberately short. The spine above is yours to own. Read these to go deeper on the method, not to learn it.*

- [The Threat Modeling Manifesto](https://www.threatmodelingmanifesto.org/) (~15 min) — the four questions and the values, in two pages. Read it first; it's the whole philosophy distilled.
- [OWASP Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html) (~30 min) — a working method you can apply today; read the "Decompose" and "Determine threats" sections closely.
- [Microsoft — STRIDE threat categories](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats) (~20 min, reference) — a clean catalog of what each letter looks like in practice; map your boundaries against it.
- [Adam Shostack — Elevation of Privilege (free STRIDE card game)](https://shostack.org/games/elevation-of-privilege) (~30 min, play one round) — learn STRIDE by playing it against a design; genuinely the fastest way it clicks.

## Key concepts
- A **trust boundary** is where data crosses from less-trusted to more-trusted — and where most bugs live
- Threat modeling = four questions: what are we building · what can go wrong · what do we do · did we do well
- **STRIDE** makes "what can go wrong" systematic: Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege
- STRIDE maps onto first principles: spoofing↔auth, tampering↔integrity, disclosure↔confidentiality, elevation↔authorization
- The cheapest bug to fix is the one still on the whiteboard — model before you reach for a tool
- A compliance checklist asks "do you have X?"; a threat model asks "where can it go wrong, and do you defend each crossing?"

## AI acceleration
Hand a model your data-flow description and ask for a STRIDE pass — it produces a fast, confident draft
of plausible threats. That draft is a brainstorming partner, not a model. The skill, and your job, is
**pruning**: discard the threats that don't apply to *your* system, add the context-specific ones it
can't know (your real trust boundaries, your business logic), and own the final one-pager. An unpruned
threat list is noise; judgment is what turns it into a model. Note in your deliverable what you cut and
what you added — that record *is* the evidence you did the thinking.
