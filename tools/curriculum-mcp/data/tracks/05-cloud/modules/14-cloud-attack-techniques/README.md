# Module 14 — Cloud Attack Techniques

*Variant D · breach-driven, predict-the-blast-radius / detonate (purple-team — pure attack, no fix half by design). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Cloud & Container Security** — *a cloud attack is not an exploit; it's a login. The adversary uses your services exactly as designed — your only edge is the trail those API calls leave.*

<!-- module-meta -->
**Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~4–6 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 02 — Cloud Identity & IAM](../02-cloud-identity-iam/README.md) · [Module 03 — IAM Attack Paths](../03-iam-attack-paths/README.md)
{ .module-meta }


## The case

On 25 August 2022, LastPass disclosed that an attacker had stolen source code from its development
environment. That sounded contained. It wasn't. Months later — in the
[December 2022 update](https://blog.lastpass.com/posts/notice-of-recent-security-incident) and the more
detailed [March 2023 post-mortem](https://blog.lastpass.com/posts/security-incident-update-recommended-actions) —
LastPass revealed a **second** intrusion that reused what was taken in the first. The attacker
compromised the **home computer of one of four senior DevOps engineers** who held the keys to LastPass's
backups, planted a keylogger (via an unpatched [CVE-2020-5741](https://nvd.nist.gov/vuln/detail/CVE-2020-5741)
in Plex), and captured the engineer's master password. With it they opened that engineer's corporate
vault and lifted the **decryption keys for the production backups** — which lived in **Amazon S3 and
DynamoDB.** Between 20 August and 16 September 2022 they used valid credentials and **assumed IAM roles**
to read those backups and **exfiltrate customer vault data** to storage they controlled.

There was no zero-day in AWS. Every step — the login, the `AssumeRole`, the `GetObject`, the copy to an
external account — was a **signed, authorized API call**. LastPass's own
[Wikipedia-summarized timeline](https://en.wikipedia.org/wiki/2022_LastPass_data_breach) notes the
behaviour was eventually caught by **GuardDuty alerts** on anomalous IAM role use — meaning the signal was
*there*, in CloudTrail, the whole time. This is the identity-first cloud playbook that
[Scattered Spider / LUCR-3](https://permiso.io/blog/lucr-3-scattered-spider-getting-saas-y-in-the-cloud)
runs at scale and that [CISA documented in AA23-320A](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-320a):
no malware, no scripts — just the victim's own tools, used as designed.

So the question this module turns on is not "how do I break in." You already have the credentials. It's:

> **You're going to run the three moves LastPass's attacker ran — log in with valid creds, pull the data,
> stage it elsewhere. Of those three, which one screams in CloudTrail, and which is nearly silent?**

## Your job

This is a **purple-team** module: you'll **detonate** real ATT&CK-for-Cloud techniques in a safe range
and **capture the telemetry each one generates** — the raw signal a defender needs. By the end you'll
have fired, at minimum, **T1078.004 (Valid Cloud Accounts)**, **T1530 (Data from Cloud Storage)**, and
**T1537 (Transfer Data to Cloud Account)** with Stratus Red Team and Pacu, mapped each to its technique
ID, and produced an annotated **detonation log + ATT&CK mapping + captured CloudTrail events.** That
telemetry is not the end of the story — it is the literal *input* to module 15 (write the detection) and
module 16 (reconstruct the incident). You are manufacturing the attack so the defender across the hall
has something real to catch.

## The loudness question — think before the lab

Don't skip this. Rank the three techniques by how loud each is in CloudTrail *before* you detonate
them — being wrong is the teaching event, and the lab will grade your ranking.

> **The mental model:** every technique here is a `signed API call`, and a *management-plane* call (one
> that changes the account — `AssumeRole`, `PutBucketReplication`) is recorded by CloudTrail **by
> default**. A *data-plane* call (one that just touches an object — `GetObject`) is **not logged unless
> you turned on S3 data events**, which most accounts don't. That single distinction — management plane
> logged by default, data plane silent by default — decides which of LastPass's three moves left the
> loudest trail and which the attacker could run almost invisibly. (T1078.004's `AssumeRole`: loud,
> always recorded. T1530's mass `GetObject`: *silent* unless data events are on — this is the gap.
> T1537's `PutBucketReplication`: loud, and the destination-account ID is right there in the event.)

You'll confirm or correct that ranking against real captured events in the lab. The point isn't trivia:
**the technique that's hardest to detect is the one the defender most needs you to have detonated**, so
they can prove their detection works (or discover it can't fire because the log was never collected).

## ATT&CK for Cloud is the shared vocabulary

The reason you map each detonation to a technique ID is that **module 15 and 16 speak the same
language.** A detonation log that says "I ran some S3 commands" is useless to a detection engineer; one
that says "T1530, eventName `GetObject`, 47 calls in 30s, assumed-role identity, non-app user-agent" is a
detection spec. The three techniques are a compressed cloud kill chain — **access → collect → stage** —
and the analytical edge in each is never one field. T1530 isn't "a `GetObject` happened" (those happen
constantly); it's the *combination*: which identity, what rate, which user-agent, how broad the object
spread. Capturing that combination cleanly is the whole job of this module.

## Learn (~3 hrs)

*Richer than a foundations module — this is the purple-team craft, and the tool docs are genuinely the
best public reference for what each attack looks like in the logs. Read the case first.*

**ATT&CK for Cloud — the technique cards (~1 hr)**
- [ATT&CK Cloud Matrix](https://attack.mitre.org/matrices/enterprise/cloud/) (~20 min) — orient on Initial Access, Credential Access, Collection, Exfiltration. The *Procedure Examples* column is where you see the real API calls.
- [T1078.004 — Valid Accounts: Cloud Accounts](https://attack.mitre.org/techniques/T1078/004/) (~15 min) — read the **Detection** section: it names the exact log sources. This is LastPass's entry move.
- [T1530 — Data from Cloud Storage](https://attack.mitre.org/techniques/T1530/) (~10 min) — note *why* this is hard to see: the control-plane-vs-data-plane logging gap is called out here.
- [T1537 — Transfer Data to Cloud Account](https://attack.mitre.org/techniques/T1537/) (~10 min) — the exfil-to-external-account move; the destination account is the tell.

**The detonation tools (~1 hr)**
- [Stratus Red Team — attack technique list](https://stratus-red-team.cloud/attack-techniques/list/) (~25 min) — browse the AWS techniques; each card gives the detonation, the exact API calls fired, **and a sample CloudTrail event**. Best public cloud-attack log reference there is.
- [Stratus Red Team — GitHub README](https://github.com/DataDog/stratus-red-team) (~15 min, skim) — quick-start and the endpoint/`--localstack`-style workflow you'll use in the lab.
- [Pacu — Getting Started wiki](https://github.com/RhinoSecurityLabs/pacu/wiki) (~20 min) — the `run`/`search`/`exec` model; Pacu is for *chain* reasoning (enumerate → find over-priv role → assume → re-enumerate), Stratus for *atomic* detonation.

**The adversary, for real (~30 min)**
- [Permiso — LUCR-3: Scattered Spider Getting SaaS-y in the Cloud](https://permiso.io/blog/lucr-3-scattered-spider-getting-saas-y-in-the-cloud) (~20 min) — the definitive identity-first cloud-TTP writeup; read how they use *your* tools, not malware.
- [CISA AA23-320A — Scattered Spider](https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-320a) (~10 min, skim) — the federal advisory; corroborates the vishing → valid-accounts → cloud-data pattern.

## Key concepts
- A cloud attack is a sequence of **signed, authorized API calls**, not an exploit — the adversary logs in and uses services as designed
- **Detonation = purple-teaming:** you generate real adversary telemetry in a safe range so the defender has something true to detect
- Management-plane calls (`AssumeRole`, `PutBucketReplication`) are logged by CloudTrail **by default**; data-plane calls (`GetObject`) are **silent unless S3 data events are enabled** — this is *the* detection gap
- T1078.004 / T1530 / T1537 = the compressed cloud kill chain: **access → collect → stage**
- The attack signal is a *combination* of fields (identity · rate · user-agent · object breadth), never a single one — that combination is the detection spec you hand module 15
- Pacu for attack-chain reasoning; Stratus Red Team for atomic, detection-focused technique detonation

## AI acceleration
Feed a model the Pacu session output or a batch of captured CloudTrail events and ask it to identify the
ATT&CK techniques and rank the highest-signal calls. It's a strong first-pass classifier on known
technique signatures — but it makes two errors this module trains you to catch: it **hallucinates
CloudTrail field names** that aren't in the real event, and it misses **combination logic** (event A then
event B from the same identity inside a window) because it scores fields independently. Worse for a
detection engineer, it will happily call a *data-plane* event "detected" without noticing the log was
never collected. Use it to triage; validate every claimed field against the *actual* captured event and
every technique against its ATT&CK card. You own the final mapping — module 15 builds detections on top
of it, so a hallucinated field becomes a detection that never fires.
