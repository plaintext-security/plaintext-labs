# Module 07 — Enrichment & Data Pipelines

*Type 7 · Build-&-Operate — ship a working two-stage enrichment pipeline and run it; the deliverable is the operating, scheduled pipeline feeding pre-enriched data downstream, not an essay. (Secondary: Tool-Build — the monitoring tool you package alongside it.) [Go to the hands-on lab →](lab.md)*

*Last reviewed: 2026-06*

**Security Automation** — *collection without enrichment is noise; enrichment without durability is a pipeline that loses alerts the first time an API blinks.*

<!-- module-meta -->
**Type:** Build-&-Operate (Family II) &nbsp;·&nbsp; **Difficulty:** Intermediate &nbsp;·&nbsp; **Estimated time:** ~3–4 hrs (study + lab) &nbsp;·&nbsp; **Prerequisites:** [Foundations](../../../00-foundations/README.md), [Module 04 (Configuration Management)](../04-configuration-management/README.md) (its mock enrichment service is reused here)
{ .module-meta }

## Why this matters

Security data arrives continuously and arrives raw: an alert says `source_ip 185.220.101.1, RULE-002,
HIGH` and nothing more. Before an analyst can act, that line needs *context* — is the IP a known Tor
exit, a flagged C2 node, or the office VPN? Is the asset a domain controller or a print server? That
context lives in threat-intel feeds, asset databases, and geolocation services, and stitching it onto
each event is **enrichment**. Done by hand it is the most grinding toil in a SOC: an analyst opening
VirusTotal, AbuseIPDB, and the CMDB in three browser tabs and copy-pasting one indicator at a time,
hundreds of times a shift. It does not scale, it is error-prone, and it is the first thing a tired
analyst skips at 3 a.m. A scheduled pipeline that enriches every alert *before* it reaches the queue
is the difference between analysts who spend their morning enriching by hand and analysts who start
with pre-enriched data and spend their time on decisions. That toil — and eliminating it — is the
anchor for this module; there is no breach here, only the grind that automation removes.

But the moment you automate the enrichment, you take on the failure modes of any data pipeline, and
they are not the happy-path ones a first draft handles. The enrichment API will time out. The
processor will be restarted mid-event by a deploy or an OOM kill. A malformed alert will land in the
queue. A pipeline that silently drops an alert on any of these is *worse* than the manual process it
replaced, because no human is watching the gap. The engineering judgment in this module is exactly
the set of properties that make a pipeline trustworthy when nobody is looking: **durability,
at-least-once processing, idempotency, and observability.**

## The core idea

A data pipeline is a sequence of stages that each transform data and hand it to the next. Here it is
two stages with one decoupling boundary between them: a **collector** that emits raw alerts at a
predictable rate into a queue, and a **processor** that pulls from the queue, enriches each alert
(IP reputation, asset context, a verdict), and writes the enriched result to a store. The separation
is the architecture's whole point — the collector knows nothing about enrichment, the processor knows
nothing about collection — which makes each independently testable, independently scalable, and
independently replaceable. In production the queue is Kafka, SQS, or Redis and the store is
Elasticsearch or a database; here the queue is a directory and the store is another directory, but the
*shape* — produce → queue → consume → store — is identical, and so is the judgment.

**The queue between the stages is what buys you durability, and the simplest durable queue is a
directory.** The collector writes `alert-<uuid>.json` into a `pending/` directory; the processor lists
`pending/`, enriches each file, writes the result to `processed/`, and only then deletes the original
from `pending/`. The ordering is load-bearing: *write the output, then delete the input.* If the
processor crashes after enriching but before deleting, the file is still in `pending/` and gets picked
up again on restart — nothing is lost. This is **at-least-once** delivery: every alert is processed at
least once, and the price you pay is that an event can be processed *twice* (if the crash happens
between the write and the delete). You accept duplicates and design the processing to tolerate them —
which means **idempotent** processing: enriching the same alert twice must produce the same result and
write to the same `processed/<uuid>.json`, never two divergent copies. Keying the output file by the
alert's own UUID gives you that for free. The alternative — delete the input first, then enrich — is
*at-most-once* and silently loses alerts on a crash; for security data that trade is almost always
wrong. The directory-as-queue is transparent on top of being durable: `ls pending/` shows you the
backlog, no database or admin console required.

**Failures are routed, not swallowed.** An enrichment call that times out should not crash the
processor and should not silently drop the alert — it moves the file to an `errors/` directory (a
**dead-letter queue**) where it is visible, countable, and drainable once the API recovers. A
malformed JSON file does the same. The rule is: an event leaves `pending/` only by being successfully
processed *or* by being explicitly dead-lettered — never by being lost.

**Observability is the property that makes all of the above operable, not optional.** A pipeline that
runs silently is a pipeline that fails silently — and a stuck queue you can't see is an outage you
discover from the analysts, hours late. The minimum bar: every processed event emits a structured log
line with the event ID, the verdict, and the processing time; every error emits one too. That stream
(captured by Docker's logging driver, tailable during an incident) plus a backlog you can measure
(`ls pending/ | wc -l`) is what turns "the pipeline is up" from a hope into something you can prove.

A note on the scheduler: this lab runs the loop with the `schedule` library —
`schedule.every(N).seconds.do(job)` — a readable in-process scheduler that needs no cron, Celery, or
broker. For modest throughput (a few events per second) with the directory queue providing the
durability, that is the right tool. The boundary worth knowing: for high throughput, work that must
survive across distributed workers, or fan-out/retry-with-backoff semantics, you graduate to a real
task queue (Celery + Redis, `apscheduler`, or a cloud-native queue). Reaching for Kafka on day one is
its own failure mode; choosing the right tool *for the scale you have* is part of the judgment.

## Learn (~2 hrs)

**Pipeline architecture & the decoupling boundary (~50 min)**
- [The Log: What every software engineer should know about real-time data — Jay Kreps (LinkedIn Engineering)](https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying) (~40 min, long — read parts 1–2) — the seminal essay on why a durable log/queue sits *between* producers and consumers; it is the conceptual justification for the collector/processor split you build here. Read for the "why decouple," skim the Kafka-specifics.
- [schedule — Python job scheduling for humans (docs)](https://schedule.readthedocs.io/en/stable/) (~10 min) — the exact library the lab uses; read "Examples" and "Common Issues" only. Short by design; note the line in the docs about it *not* being for high-throughput or persistence — that is the boundary called out above.

**Durability, at-least-once & idempotency (~45 min)**
- [Idempotent Receiver — Patterns of Distributed Systems, Martin Fowler / Unmesh Joshi](https://martinfowler.com/articles/patterns-of-distributed-systems/idempotent-receiver.html) (~20 min) — *why* at-least-once delivery forces idempotent processing, and how a receiver de-dupes. The directory-as-queue keyed by UUID is a concrete implementation of exactly this pattern.
- [Amazon SQS — message lifecycle & dead-letter queues (AWS docs)](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) (~15 min) — read the dead-letter-queue section; the production framing of the `errors/` directory you build (poison messages routed aside, not dropped, so the queue keeps moving). Maps the lab's pattern onto a tool you'll meet in the field.
- [Python logging — Logging HOWTO (Python docs)](https://docs.python.org/3/howto/logging.html) (~10 min) — read "When to use logging" and "Logging to stdout"; structured, per-event log lines are how a running pipeline becomes observable. (We log to stdout so Docker captures it.)

## Key concepts
- **Collector / processor separation:** one decoupling boundary (the queue) makes each stage independently testable, scalable, and replaceable.
- **Directory-as-queue for durability without a database:** `pending/` → `processed/`, with `errors/` as the dead-letter queue; `ls pending/` *is* your backlog metric.
- **Write-output-then-delete-input → at-least-once:** crash-safe, at the cost of possible duplicates.
- **Idempotent processing:** key the output by the alert UUID so re-processing is harmless — the price you pay for at-least-once.
- **Failures are routed, not swallowed:** timeouts and malformed events go to `errors/`; an event leaves `pending/` only by success or explicit dead-letter.
- **Observability is not optional:** every event gets a log line (ID, verdict, duration); a silent pipeline fails silently.
- **`schedule` up to its limit:** right for modest throughput; know when to graduate to a real task queue.

## AI acceleration
A model will write the collector and processor in seconds — and the part it writes is the happy path,
which is exactly the part that was never the problem. The posture holds: **AI authors → you review
every line → you own it**, and for a pipeline the review has a concrete shape, because the bugs are all
in the failure modes the first draft skips. Ask the model for the polling loop *with* error handling,
then go hunting for what it still got wrong: Does `json.loads()` on a malformed file crash the whole
loop, or log-and-skip? Does a timed-out enrichment lose the alert, or move it to `errors/`? Does it
delete the input *before* writing the output (silent data loss on a crash), or after (durable)? Does
re-processing the same UUID make a duplicate? Then *prove* your version by breaking it on purpose —
`docker compose stop threat-api` and watch where the alerts go; drop a `not-json` file in `pending/`
and watch the loop survive. The model's first draft handles the demo; you own the version that handles
the API being down and the disk being full.
