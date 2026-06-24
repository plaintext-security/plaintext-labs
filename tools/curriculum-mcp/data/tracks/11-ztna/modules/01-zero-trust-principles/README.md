# Module 01 — Zero Trust Principles

*Variant D · concept autopsy, predict-then-reveal. [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Zero Trust Network Access** — *the perimeter didn't fail; it dissolved — and the model that replaced it starts by trusting nothing, learned by taking one famous breach apart.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }

## Why this matters

For most of network-security history, the working assumption was that everything inside the firewall
was relatively safe and everything outside was not. That model was workable when "inside" was a
data-centre you controlled and "outside" was the open internet. It stopped being workable the moment
applications moved to SaaS, infrastructure moved to cloud, and the workforce moved home. Today the
average enterprise has no single perimeter worth defending — it has dozens of identity providers,
hundreds of SaaS apps, thousands of remote endpoints, and contractors who never touch the corporate
LAN. "Inside the network" no longer means anything coherent, and yet most access models still behave
as if it does. Zero Trust is the architectural response to that fact — and the cleanest way to learn
*why* it exists is to take apart a breach that the perimeter model couldn't have stopped.

## Objective

Use a real lateral-movement breach to derive the Zero Trust tenets from first principles — name the
exact place where "inside = trusted" failed at each step — then map those failures onto the five
NIST SP 800-207 pillars and produce a gap-analysis + roadmap a security architect could act on.

## The case

On April 29, 2021, the **DarkSide** ransomware group logged into Colonial Pipeline's network — the
company that carries ~45% of the U.S. East Coast's fuel — using a single set of valid credentials
for a **legacy VPN account**. They didn't exploit a zero-day. They didn't phish their way past a
clever control. They *logged in*.

The chain, drawn from CEO Joseph Blount's June 2021 Senate testimony and the public reporting around
it, was roughly this:

1. The entry point was an old remote-access **VPN profile** that was no longer actively used but was
   still **enabled**. Crucially, that profile did **not require multi-factor authentication** — a
   password was the only gate.
2. The password turned up in a batch of **leaked credentials on the dark web**, consistent with an
   employee having reused it on some other, separately-breached account. One reused password, no
   second factor, and the attacker had a valid remote session.
3. Once on the VPN, the attacker was *inside* — and inside meant **trusted**. The interior was flat
   enough that a foothold became reach: the operators pulled ~100 GB of data and detonated ransomware,
   and Colonial pre-emptively shut down the pipeline. Fuel shortages and panic-buying hit the
   Southeast for days.

(Two older breaches show the same shape and are worth holding alongside it: **Target 2013**, where
attackers entered through an HVAC *vendor's* stolen credentials and crossed a flat interior into the
point-of-sale network; and **OPM 2015**, where a foothold in a contractor-adjacent system led to the
exfiltration of ~21.5 million background-investigation records. Different entry, same lesson: the
wall held at the edge and there was nothing behind it.)

## Call it before you read on

Don't scroll. Write down one answer — being wrong here is the entire point; it's what makes the
lesson stick.

> **The Colonial VPN required a password to get in. The perimeter *did* its job — it asked for
> credentials. So wasn't the perimeter holding? Where, exactly, did the security model fail?**

Most people name the obvious villain: "the VPN had no MFA." That's a real failure — hold it. But
notice it only explains how the attacker got *one* foothold. It does not explain how one foothold
became the whole network.

## The reveal — "inside = trusted" is the bug

The perimeter was not holding, because **the perimeter model itself is the failure here, not a
control that happened to break.** The VPN did exactly what a perimeter is designed to do: it
authenticated once, at the edge, and then placed the session *inside*, where the working assumption
is "you're on the network, so you're trusted." That single assumption is what turned one stolen
password into a national fuel crisis. The tenets below aren't a vendor checklist — they're the
**lenses** that let you see why a perimeter + a trusted interior is a structurally fragile design.

**The unit of access is the request, not the session.** The founding insight of Zero Trust — Google's
2014 **BeyondCorp** work, later formalized by **NIST SP 800-207** — is that "put the user on the
network" is the wrong unit of access. The VPN grants you a *session* on the interior and then stops
asking questions. Under ZT, the unit is **the individual request**, re-evaluated every time against
the identity making it, the device it came from, the sensitivity of the resource, and the context of
the moment. With Colonial, a per-request model would have forced the attacker to *keep* proving who
they were, on a device the org could vet, for every resource — instead of buying the whole interior
with one login.

**Verify explicitly, every time — identity *and* device.** "It required a password" is single-factor
authentication evaluated once. ZT says verify *explicitly*: a strong identity assertion (MFA, FIDO2,
mTLS, a short-lived token) **and** a signal about the device's posture (is it managed? patched?
enrolled in EDR?), checked at the time of the request, not assumed from the subnet. A legacy account
with no MFA on an unknown machine is precisely the case explicit verification is built to reject.
This is also the most common first-pass ZT mistake: **identity alone is not enough.** A stolen
credential on a trusted device is bad; the same credential on an unmanaged, compromised box is
catastrophic — and an identity-only model can't tell the two apart. CISA's Zero Trust Maturity Model
distinguishes Traditional / Advanced / Optimal largely on this point.

**Assume breach, and minimize blast radius.** The Colonial interior was flat: a foothold reached far
more than it should have. ZT's third move is to *assume the attacker is already inside* and design so
that it barely matters — least privilege, no standing trust, segmentation so server-to-server paths
that have no business existing simply don't. The goal is **not** maximum friction or inspecting every
packet; it is shrinking what any one compromised credential or device can touch. Target 2013 and OPM
2015 are the same failure mode: the wall held at the edge, and the flat interior did the attacker's
work for them.

**The model to keep:** *trust is never granted by location.* "Inside the network" is not a security
property — it is the bug Zero Trust removes. Every access decision should re-derive trust from
identity, device, and context, and grant the minimum for that one request. If your answer was "no
MFA on the VPN," you named the open door — and missed the design that let one open door own
everything behind it. That gap is exactly what this module, and this whole track, closes.

## Learn (~3 hrs)

*Short on purpose. The autopsy above is the spine; read these to deepen the mechanism, not to
relearn the model.*

**The breach, from the primary source (~30 min)**
- [Joseph Blount (Colonial Pipeline CEO) — Senate Homeland Security Committee testimony, June 8, 2021](https://www.hsgac.senate.gov/hearings/threats-to-critical-infrastructure-examining-the-colonial-pipeline-cyber-attack/) — the hearing where Blount confirmed the entry was a legacy VPN profile *without* MFA and that the password was a single factor. Watch/read for his own description of how the account was reached. This is your evidence file for the lab.
- [CISA & FBI — DarkSide Ransomware joint advisory (AA21-131A)](https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-131a) — the government technical advisory on the DarkSide TTPs, including initial access via exposed/weakly-protected remote services and post-foothold lateral movement. Read the "Technical Details" and "Mitigations" sections.

**The principles (~1.5 hrs)**
- [BeyondCorp: A New Approach to Enterprise Security (Ward & Beyer, 2014)](https://research.google/pubs/beyondcorp-a-new-approach-to-enterprise-security/) — the founding paper; ~10 pages. Read it first among the principles. Everything in the ZT space is downstream of this work, and the practitioner vocabulary comes from here. Watch for the line that the VPN-as-access-unit is the thing being rejected.
- [NIST SP 800-207: Zero Trust Architecture (2020)](https://csrc.nist.gov/pubs/sp/800/207/final) — the authoritative U.S. specification. Read **sections 1–3** (the abstract model and the seven tenets) and **section 7** (deployment scenarios). The rest is reference. The seven tenets are the rubric you'll map the breach onto.

**Policy and maturity model (~1 hr)**
- [CISA Zero Trust Maturity Model v2.0 (2023)](https://www.cisa.gov/sites/default/files/2023-04/zero_trust_maturity_model_v2_508.pdf) — the five-pillar maturity model. Read the executive summary and the maturity table for each pillar. This is the framework practitioners use to benchmark where an org actually stands, and what "moving one pillar up a level" concretely means.

## Key concepts

- "Inside the network" is not a security property — location-based trust is the bug Zero Trust removes
- The unit of access is the individual **request**, re-evaluated each time — not the VPN **session** (BeyondCorp)
- Verify explicitly: a strong identity assertion **and** a device-posture signal — identity alone is insufficient
- Assume breach; design to minimize **blast radius** (least privilege, segmentation), not to maximize friction
- The seven NIST 800-207 tenets and the five pillars: identity, device, network, application/workload, data
- CISA's three maturity levels per pillar: Traditional → Advanced → Optimal
- One reused password + no MFA + a flat interior = **one credential owns the whole network** (Colonial 2021)

## AI acceleration

Hand a model the public Colonial Pipeline timeline (or the Target / OPM ones) and ask it to map each
failure to a Zero Trust tenet *before* you write yours. It produces a fast, confident draft — and a
good one to check, because models tend to collapse the story into the single headline cause ("they
had no MFA") and stop there. Your job is to catch what it flattened: the quieter, structural failure
is the **flat interior** that turned one foothold into the whole network (assume-breach /
blast-radius), and the conflation of ZT marketing language ("we have SSO, so we did Zero Trust") with
the actual NIST tenets. Verify every gap claim is traceable to a specific NIST 800-207 tenet or CISA
maturity level before committing the deliverable. If you can explain *why* the breach needed both the
open door **and** the flat interior, not just the missing MFA, you've learned the module — and you
own the verdict.
