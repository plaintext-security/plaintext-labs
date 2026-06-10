# Module 07 — Enrichment & Data Pipelines

*Module concept · [Go to the hands-on lab →](lab.md)*


**Security Automation** — *collection without enrichment is noise; enrichment without collection is trivia.*

## Why this matters
Security data arrives continuously: alerts from the SIEM, logs from endpoints, events from cloud
APIs. Enrichment — adding context from threat-intel, asset databases, and geolocation — is what
transforms a raw event into something an analyst can act on. A scheduled enrichment pipeline
that runs every five minutes is the difference between analysts who spend their morning
enriching alerts by hand and analysts who start with pre-enriched data and spend their time on
decisions.

## Objective
Build a two-container pipeline: a collector that generates alert JSON at intervals, and a
processor that enriches and stores each alert — using the `schedule` library and the enrichment
function from module 04.

## The core idea
A data pipeline is a sequence of steps that each transform data and hand it to the next step.
The collector's job is to emit raw events at a predictable rate into a queue (here, a shared
volume or a Unix socket — in production, Kafka, SQS, or Redis). The processor's job is to pull
from the queue, enrich each event (add IP reputation, asset context, geolocation), and write the
enriched event to a store (here, a JSON file; in production, Elasticsearch or a database). The
separation is important: the collector doesn't know anything about enrichment; the processor
doesn't know anything about collection. This makes both components independently testable and
replaceable.

The `schedule` library gives you `schedule.every(30).seconds.do(job)` — a simple, readable
scheduler that runs inside a Python process without needing cron, Celery, or an external
scheduler. For pipelines with modest throughput (a few events per second) and no persistence
requirement, `schedule` running in a loop is the right tool. For higher throughput, persistence
across restarts, or distributed workers, you'd reach for a proper task queue (Celery + Redis,
`apscheduler`, or cloud-native schedulers). Know the boundary so you choose the right tool.

State management is where simple pipelines become complex: what happens when the processor
restarts mid-event? What if the enrichment API is down for two minutes — are those events lost?
The simplest durable pattern is a "work queue" implemented as a directory: collector writes
`event-<uuid>.json` to a `pending/` directory; processor picks up files, enriches them, writes
to `processed/`, and deletes from `pending/`. If the processor crashes mid-enrichment, the file
remains in `pending/` and is retried on restart. This pattern requires no database and is
transparent (you can `ls pending/` to see the backlog).

Observability is not optional for production pipelines: every event processed should produce a
log line with the event ID, the enrichment verdict, and the processing time. A pipeline that
runs silently is a pipeline that fails silently. The minimal observability requirement: log
every input, every enrichment result, and every error to stdout — so Docker's logging driver
can capture it and you can tail the logs during a live incident.

## Learn (~2 hrs)

**Pipeline architecture (~1 hr)**
- [The Log: What every software engineer should know about real-time data (Jay Kreps)](https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying) — the seminal post on log-based data pipelines; long but worth it for understanding why the collector/processor separation exists.
- [schedule — Python scheduling library (docs)](https://schedule.readthedocs.io/en/stable/) — the library used in this lab; read the "Example" and "Decorator" sections; it's simple and the docs are short.

**Durable pipelines (~1 hr)**
- [Work queues with directory patterns — Martin Fowler (background reading)](https://martinfowler.com/articles/patterns-of-distributed-systems/idempotent-receiver.html) — the idempotent receiver pattern; the directory-as-queue approach in this lab is a concrete implementation.
- [Python logging — Logging HOWTO (Python docs)](https://docs.python.org/3/howto/logging.html) — read the "Logging to a file" and "When to use logging" sections; structured log output is how you observe a running pipeline.

## Key concepts
- Collector / processor separation: single responsibility, independently replaceable
- `schedule` for simple intervals: `every(N).seconds.do(job)` — right up to its limits
- Directory-as-queue: `pending/` → `processed/` for durability without a database
- Every event gets a log line: event ID, verdict, duration, errors
- Observability is not optional — silent pipelines fail silently

## AI acceleration
A model will write the collector and processor quickly. The missing pieces are always error
handling and observability: what happens if the enrichment call times out? Is the event lost?
What if the `pending/` directory doesn't exist on startup? Ask the model to handle these cases,
then test them: kill the enrichment API mid-run and watch what happens to the pipeline. The
model's first draft handles the happy path; you own the version that handles reality.
