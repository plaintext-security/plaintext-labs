# Module 01 — Cloud Fundamentals & Shared Responsibility

*Variant D · breach-driven, predict-then-reveal, interleaved ("render the verdict"). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Cloud & Container Security** — *every cloud breach ends in one question: provider's fault or yours? Learn to answer it by answering a real one.*

<!-- module-meta -->
**Difficulty:** Beginner–Intermediate &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md)
{ .module-meta }


## The case

On 19 July 2019, an external researcher emailed Capital One: your customer data is on the open
internet. By the time it was contained, **roughly 100 million US credit-card applications** — names,
addresses, SSNs, bank account numbers — had been copied out of Amazon S3. The chain, later laid out in
the [DOJ indictment](https://www.justice.gov/usao-wdwa/press-release/file/1188626/download) and the
[US Senate report](https://www.hsgac.senate.gov/wp-content/uploads/imo/media/doc/Capital%20One%20Report.pdf),
went like this:

1. A misconfigured web-application firewall let an attacker make the server **fetch a URL of their
   choosing** (a server-side request forgery).
2. They pointed it at the **instance metadata service** — a special address every EC2 box can reach —
   and it handed back the **temporary credentials of the server's IAM role.**
3. That role was allowed to **`s3:List*` and read *every* bucket in the account**, not just the one it
   needed.
4. The data was **encrypted at rest**. They walked out with it anyway.
5. The activity was in **CloudTrail the whole time.** Nobody was watching; an outsider reported it.

This was not an AWS breach. AWS ran exactly as designed at every step. So here is the question this
entire module — and your whole career in cloud security — turns on:

> **At each link in that chain, whose control failed: Amazon's, or the customer's?**

## Your job

By the end of this module you'll **render a verdict** on a real breach chain: for each hop, name the
owner of the failed control (provider vs. customer), the plane it lived on (who-can-call vs.
what-flows), and the single configuration change that would have broken the chain there. You'll
reproduce the *responsibility conditions* of two hops in a local account so the judgment is yours, not
borrowed — the exact skill a cloud incident responder or GRC analyst is paid for.

## Call it before you read on

Don't scroll to the answers. Write down your gut verdict on these three — you'll grade yourself in a
moment, and again in the lab. Being *wrong* here is the point; it's what makes the reveal stick.

> **Q1.** The 100M records were **encrypted at rest**, and the attacker still read them in plaintext.
> Did the encryption do anything? Whose control was supposed to stop this?
>
> **Q2.** The stolen credentials came from the **instance metadata service — a feature Amazon builds
> and runs.** Does that make this hop Amazon's failure?
>
> **Q3.** Add it up across all five hops: **how many were Amazon's responsibility?**

## The model, revealed

Hold your three answers against these. The shared responsibility model is usually drawn as a single
diagram — provider below the line, customer above it. That picture is true but useless, because it
hides the only thing that matters in an incident: **where the line actually sits for *this* control.**
Here's where it sat for Capital One.

**Q1 — the encryption that didn't matter.** Encryption at rest is the control everyone *feels* is
"handled by AWS," and in a sense it is: AWS makes it nearly free to turn on. But it defends against a
specific threat — someone stealing the physical disk or the raw storage. It does **nothing** against a
principal the account *authorized* to read the data, because that principal's reads are decrypted
transparently. The over-permissioned role *was* authorized. So the failed control wasn't encryption at
all — it was **who was allowed to use the key and the bucket**, which is identity, which is the
customer's. **The mental model to keep: encryption protects data from people without keys; it is
silent against people you gave keys to.** The customer owned that, and it was wide open.

**Q2 — the line is finer than the diagram.** The metadata service is Amazon's — it exists, it works,
it did its job. But *whether that server should have been allowed to ask it for credentials over an
unauthenticated request*, and *how powerful the credentials it returned were*, are both customer
settings (enforcing IMDSv2; scoping the role). This is the move that separates someone who *understands*
shared responsibility from someone who recites it: **the provider can own the mechanism while the
customer owns the configuration of that same mechanism.** The line doesn't run between *services*. It
runs *through* them. Capital One didn't enforce IMDSv2 and didn't scope the role — both their side of a
line that runs straight through an AWS feature.

**Q3 — the answer is zero.** Walk the whole chain and every wall that gave way was a customer control
left in a permissive or unmonitored state: the WAF config, IMDSv2 not enforced, the over-broad role,
detection nobody wired up. Amazon's surface — the hypervisor, the metadata service, S3's durability,
CloudTrail's recording — held end to end. **That is the entire lesson of shared responsibility, and the
reason "the default is not secure" is the most expensive sentence in cloud:** the breaches that look
like provider failures are almost always customer-owned controls that *felt* like provider territory.
If you predicted "one or two were Amazon's," you've just felt exactly the misconception this module
exists to correct — and you'll feel it again, hands-on, in the lab.

Two of those hops — the over-broad role reading every bucket (Q1's real cause) and the
"encryption didn't help" twist — you'll reproduce in a local account and verdict yourself. The point
isn't to re-exploit Capital One; it's to make the *judgment* muscle memory.

## Learn (~2 hrs)

*Deliberately short. This is a foundations module: the spine above is yours to own, not to outsource to
a tour of five sites. Read these to go deeper on the mechanism, not to learn the model.*

- [AWS Shared Responsibility Model](https://aws.amazon.com/compliance/shared-responsibility-model/) (~30 min) — the primary source. Read it *after* the case above and notice how few "secure" boxes are actually AWS's.
- [Krebs on Security — the Capital One breach, explained](https://krebsonsecurity.com/2019/08/what-we-can-learn-from-the-capital-one-hack/) (~20 min) — the clearest public walk-through of the chain; corroborates the brief above with a second source.
- [AWS — Use IMDSv2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html) (~20 min, skim) — read *why* IMDSv2 exists: it's the customer control that would have broken hop 2. The page is literally Capital One's lesson turned into product.
- [MITRE ATT&CK for Cloud — tactics](https://attack.mitre.org/matrices/enterprise/cloud/) (~15 min, orient only) — skim the columns and ask which side of the line each tactic attacks.

## Key concepts
- The shared-responsibility line runs *through* services, not just between them — provider owns the mechanism, customer owns its configuration
- Encryption at rest is silent against an authorized, over-permissioned principal — identity is the real control
- "Default is not secure": the breaches that look like provider failures are usually customer controls left permissive
- Control plane (who can call: IAM, role scope) vs. data plane (what flows: bucket reads, exfil) — a chain crosses both
- Rendering a per-hop responsibility verdict is the core skill of cloud IR and GRC

## AI acceleration
Hand a model the public Capital One post-mortem and ask it to produce the per-hop responsibility verdict
*before* you write yours. It's a fast, confident draft — and a perfect adversary to check, because it
reliably makes the two errors this module is about: it will often say "the data was encrypted, so it was
protected" (Q1 — false) and lean toward blaming "the AWS metadata service" (Q2 — wrong owner). Your job
is to catch exactly those misattributions. If you can explain *why* the model put the line on the wrong
side, you've learned the module. You own the verdict.
