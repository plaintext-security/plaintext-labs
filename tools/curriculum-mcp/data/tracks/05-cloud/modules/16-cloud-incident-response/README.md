# Module 16 — Cloud Incident Response

*Variant D · breach-driven, predict-what-fires / reconstruct ("the log is the crime scene — rebuild the timeline"). [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Cloud & Container Security** — *the attacker left in the API log; cloud IR is reconstruction from an immutable record, not disk forensics. This is the payoff — everything the track taught, run under pressure.*

<!-- module-meta -->
**Difficulty:** Intermediate–Advanced &nbsp;·&nbsp; **Estimated time:** ~4.5–6.5 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md) · [Module 14 — Cloud Attack Techniques](../14-cloud-attack-techniques/README.md) · [Module 15 — Logging & Detection](../15-cloud-logging-detection/README.md)
{ .module-meta }


## The case

In August 2022, LastPass disclosed that an attacker had breached its **development environment** via a
compromised engineer's laptop and stolen **source code and proprietary technical information.** The
company investigated, said the attacker's access had been **contained**, that no customer vault data was
taken, and — by early September — declared the incident closed.

It was not closed. In a [later, much longer disclosure](https://blog.lastpass.com/posts/2022/12/notice-of-recent-security-incident),
LastPass revealed a **second** intrusion that ran from roughly **August into October 2022**. The
attacker had taken the **technical information exfiltrated in the first incident** — source code, internal
documentation, knowledge of how the systems fit together — and used it as **reconnaissance** to target a
*specific* senior DevOps engineer, one of only four people who held the keys to the company's encrypted
backup storage. They compromised that engineer's **personal home computer** (via a vulnerable third-party
media-player package), keylogged the master password to a corporate vault, and from there reached the
**decryption keys for the cloud-based backup buckets** — and copied out customer vault backups and
configuration data. (LastPass laid the full chain out in its
[security-incident updates](https://blog.lastpass.com/posts/security-incident-update-recommended-actions).)

So the first incident *was* contained, in the narrow sense — the attacker was evicted from the dev
environment. And yet it directly enabled the second. Before you read on, this is the question the whole
module turns on:

> **The first breach looked "contained." What did the responders miss that let the same actor come back
> three months later and reach the crown jewels?**

## Your job

By the end of this module you'll do the thing a cloud incident responder is actually paid for: take a raw
**CloudTrail export** (and the flow logs beside it), **reconstruct a defensible timeline** — who did what,
when, in what order — **pull the IOCs**, **scope the blast radius**, and **contain in the right sequence.**
Then you'll do the part that makes it repeatable: **extend a triage script** so the reconstruction is
automated — the super-timeline move, sorting heterogeneous events by their one shared key, *time*. Your
deliverable is a real IR artifact: the timeline, the IOC set, and the automation that builds them.

## Call it before you read on

Don't scroll. Commit a verdict — being wrong here is the teaching event, and you'll test it in the lab.

> **Q1.** The first-incident responders removed the attacker's access to the dev environment and saw no
> further activity. Why was that *not* enough — what survives an eviction?
>
> **Q2.** The crown-jewel data (the customer vault backups) lived in cloud buckets and was **encrypted at
> rest.** The attacker walked out with it anyway. (Where have you seen this exact twist before?) What was
> the actually-failed control?
>
> **Q3.** You're handed a raw CloudTrail export of a cloud incident. What is the *first* question you ask
> of it — before you read a single event?

## The reconstruction, revealed

Hold your answers against these.

**Q1 — containment is not eradication; exfiltrated data is now attacker capability.** The responders
removed *access*, which is necessary and feels like the finish line. But the first breach's loot was
**information** — source code and architecture docs — and you cannot revoke information once it's copied
out. That stolen knowledge became the *recon phase* of the next intrusion: it told the attacker exactly
which four engineers to target and which one's machine was the soft path to the backup keys. **The mental
model: once data leaves, treat it as a permanent increase in the adversary's capability, and scope your
response to what that data *enables*, not just to where the attacker currently sits.** "We evicted them"
answers a smaller question than "what did they take, and what does taking it let them do next?" The
LastPass first-incident response answered the small question. (This is the same containment≠eradication
gap that lets ransomware actors who were "kicked out" return through a backdoor they planted — the eviction
was real; the eradication was not.)

**Q2 — encryption at rest is silent against an authorized principal.** You met this exact lesson in
Module 01 with Capital One, and it recurs here because it is the most expensive misconception in cloud:
encryption protects data from people *without* the key. The attacker didn't break the encryption — they
**stole the decryption keys** by compromising an engineer who legitimately held them. To the storage
layer, the reads looked authorized, because they *were*. The failed control was never the cipher; it was
the **blast radius of a single human's credentials** reaching both a home machine and the production key
material — identity and segmentation, the customer's side of the line. If you predicted "the encryption
protected the backups," you just felt the misconception the track has hammered from module one.

**Q3 — "is the trail intact?"** This is the reconstruction discipline, and it's why cloud IR has a
different shape than endpoint forensics. There is no disk to image, no memory to dump — the **entire crime
scene is an immutable, structured, per-event API log.** CloudTrail (and its GCP/Azure equivalents) is your
ground truth, so the first move is always to ask whether it's *whole*: a competent attacker calls
`StopLogging` early, and the **gap that creates is itself evidence** — its start, end, and duration are
data. Once you trust the trail, IR becomes a **reconstruction problem**: thousands of authenticated calls,
your job is to turn them into a narrative a court or a CISO would accept. The technique is the
**super-timeline** — take every heterogeneous source (control-plane CloudTrail, data-plane flow logs,
later GuardDuty findings) and **merge them on the one field they all share: time.** Sort by timestamp, tag
each event with its kill-chain phase, filter to the attacker's identity and source IPs, and the raw log
becomes a readable order of operations: *credential check → enumeration → role assumption → collection →
exfil channel opened → trail stopped → persistence key minted.* That ordered story **is** the incident
report; the log records are the evidence under it. The methodology is exactly what timeline tools like
**hayabusa** do for Windows event logs (ingest, sort, tag, output a sorted timeline) — the source changes,
the move doesn't.

The two halves you'll reconstruct in the lab — the **timeline from CloudTrail** and the **exfil
corroboration from flow logs** — are the two planes every cloud incident lives on. Control plane tells you
*what API was called by whom*; data plane tells you *how many bytes left, to where*. An `AssumeRole` + mass
`GetObject` in CloudTrail that lines up with a hundreds-of-megabyte outbound flow to an external IP is a
**defensible exfiltration finding.** Either alone is a lead; together they're a verdict.

## Learn (~3.5 hrs)

*The track's last module before the capstone — curate a bit more, because IR pulls together identity
(02/03), logging (15), and attacker TTPs (14) all at once.*

**The case — read the primary post-mortem (~45 min)**
- [LastPass — "Notice of Recent Security Incident" + the December update](https://blog.lastpass.com/posts/2022/12/notice-of-recent-security-incident) (~30 min) — the breached company's own disclosure of the two-incident chain. Read it as an IR artifact: notice how the *first* incident's stolen data is named as the *second* incident's recon. This is your anchor; the first-party RCA is the most credible "what failed" source there is.
- [UpGuard — The LastPass Data Breach: timeline and key lessons](https://www.upguard.com/blog/lastpass-vulnerability-and-future-of-password-security) (~15 min, skim) — the engineer's home machine, the Plex keylogger, the four key-holders, the backup decryption keys. The hop-by-hop the verdict rests on.

**Cloud IR frameworks (~1 hr)**
- [AWS Security Incident Response Guide](https://docs.aws.amazon.com/security-ir/latest/userguide/welcome.html) (~40 min) — read **"Detection and Analysis"** and the forensics workflow; skip the org sections. The primary AWS source for how a cloud IR engagement is structured.
- [CloudTrail — `userIdentity` element reference](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-event-reference-user-identity.html) (~20 min) — the most forensically rich field in a record. Learn the difference between `IAMUser`, `AssumedRole`, `Root`, and `AWSService` and what each implies — the `IAMUser`→`AssumedRole` transition *is* the privilege-escalation hop in the lab.

**Timeline reconstruction (~1.5 hrs)**
- [Hayabusa — GitHub README](https://github.com/Yamato-Security/hayabusa) (~30 min) — the canonical sort-tag-output timeline tool. It targets Windows event logs, but read it for the **methodology** (ingest → Sigma-tag → sorted timeline) — that's exactly what you port to CloudTrail in the lab. Don't get lost in the Windows specifics.
- [The DFIR Report — pick one recent cloud/AWS intrusion writeup](https://thedfirreport.com/) (~1 hr) — browse for an AWS-related case; the attack chains are real, the timelines are explicit, and you'll see the super-timeline discipline applied to a genuine incident. Read it asking "what's their join key, and where's their gap?"

## Key concepts
- **Containment ≠ eradication:** removing access doesn't undo exfiltration — stolen data is a permanent capability gain; scope to what it *enables* (LastPass incident-1 → incident-2)
- **The log is the crime scene:** cloud IR is reconstruction from an immutable API log, not disk forensics — CloudTrail is ground truth, and "is the trail intact?" is the first question
- **The super-timeline:** merge heterogeneous sources (CloudTrail + flow logs + findings) on their one shared key, *time*; sort, tag by phase, filter to the attacker — that ordered narrative is the report
- **Two planes corroborate:** control-plane `AssumeRole`+`GetObject` lining up with a large data-plane outbound flow = a defensible exfiltration verdict
- **The `StopLogging` gap is evidence:** its start/end/duration are data, not absence of data
- **Encryption at rest is silent against a principal you authorized** — the attacker steals the key-holder, not the cipher (Capital One, again)
- **Containment order:** revoke credentials → close exfil channels → restore logging → scope impact — and scope *beyond* the first key (persistence: second keys, new users, modified role trust)

## AI acceleration
Feed your reconstructed timeline to a model and ask it to map each event to an ATT&CK-for-Cloud technique
and flag anything that breaks the expected order. Models are strong at pattern-matching a sequence of API
calls to technique descriptions — a genuinely useful first-pass tagger. They are weak exactly where IR
judgment lives: **temporal reasoning and attribution.** A model will happily call a key used six hours
later "the same session" when it's the persistence mechanism, and it cannot tell you whether a logging gap
is an attacker covering tracks or a benign trail rotation — that's the call you're paid to make. Use it to
draft the phase tags and technique IDs; you own the sequencing, the gap analysis, and the verdict on what
the stolen data *enables next*. The timeline you commit is your professional analysis, not the model's.
