# Module 03 — Structured Data & Reporting

*Module concept · [Go to the hands-on lab →](lab.md)*


**Python for Security** — *get the data into shape, then make it readable by a human and a machine.*

## Why this matters
Security alerts almost always arrive as JSON — from SIEMs, from APIs, from tool output. The
analyst who can read a JSON blob, filter it, deduplicate it, and produce both a CSV for the
ticket system and a readable terminal table is faster than one who pastes raw JSON into a
spreadsheet and formats by hand. This module is about the data plumbing that every security
script needs.

## Objective
Read a file of 50 simulated security alert records in JSON, filter and deduplicate them, write a
summary to CSV, and render a formatted terminal table — using `json`, `csv`, and `rich` from
the standard library and one lightweight third-party formatter.

## The core idea
`json.loads()` and `json.dumps()` are the entry and exit points for almost all security data
exchange — every REST API, every SIEM webhook, every tool that speaks JSON passes through these
two functions. The critical habit is treating the parsed structure as untrusted input: always
check that the key exists before accessing it (`.get()` with a default, or an explicit `if key
in record` check). Silently skipping a record with missing fields is almost always correct;
raising a `KeyError` on record 3 of 50 and killing the script is almost always wrong. Security
data is messy in the field; your parser must not be brittle.

Deduplication is a recurring pattern in alert pipelines: the same finding fires three times from
three sensors, and without deduplication you create three tickets for one issue. The standard
approach is to define a "fingerprint" — a tuple of the fields that make two alerts the "same
thing" (e.g., `(rule_id, source_ip, dst_port)`) — and use a `set` to track seen fingerprints
as you iterate. This is deterministic, needs no external library, and is fast enough for
hundreds of thousands of alerts in memory. For larger volumes you add a database; for this
scale, a set is right.

CSV is the lingua franca of security reporting — every ticket system, every spreadsheet, every
manager's inbox can read it. Python's `csv.DictWriter` is the correct tool: you define the
fieldnames once, write a header row, and write dictionaries. Do not build CSV by string
concatenation — the moment a field contains a comma or a newline, hand-rolled CSV breaks in
ways that are hard to spot and painful to debug.

`rich` is a single import that transforms a terminal-printed table from unreadable text into a
formatted, colour-coded table that a non-engineer can parse at a glance. The `Console` and
`Table` objects are the core API. `rich` is the right choice here because it is widely used in
the security tool ecosystem (many popular OSS tools use it), it requires no special terminal,
and its output degrades gracefully when piped. Keep the structured data pipeline and the
presentation layer separate: compute and filter first, render last.

## Learn (~2 hrs)

**JSON in Python (~30 min)**
- [json — JSON encoder and decoder (Python docs)](https://docs.python.org/3/library/json.html) — focus on `loads`, `dumps`, `load`, `dump` and the `default` parameter for custom types; read the full "Encoders and Decoders" section.

**CSV handling (~30 min)**
- [csv — CSV File Reading and Writing (Python docs)](https://docs.python.org/3/library/csv.html) — focus on `DictWriter` and `DictReader`; these are what you'll use 95% of the time.

**Terminal output with rich (~1 hr)**
- [Rich — beautiful formatting for the terminal](https://rich.readthedocs.io/en/stable/) — read the "Introduction", "Tables", and "Console" sections; that's enough to do everything in this lab.
- [Will McGugan — Building a CLI with Rich (YouTube, 18 min)](https://www.youtube.com/watch?v=4zbehnz-8QU) — concrete demonstration of Console and Table; watch the first 12 minutes.

## Key concepts
- `json.loads()` / `json.dumps()` as the standard entry/exit for security data
- Defensive key access with `.get()` — never assume a field exists
- Deduplication by fingerprint: `set` of tuples, not regex on raw strings
- `csv.DictWriter` for correct, portable CSV output
- Separating data pipeline from presentation (`rich` at the end, not in the middle)
- Progress reporting for long-running pipelines (don't leave users staring at a blank terminal)

## AI acceleration
A model will write the JSON → CSV pipeline in one pass, correctly. The value-add is asking it to
handle the edge cases: what happens with a null field? A field that contains a comma? An alert
record with an unexpected schema version? Prompt it with a realistic broken record and review
how it handles the error. The pipeline you deploy is the one that handles the weird cases, not
the happy path.
