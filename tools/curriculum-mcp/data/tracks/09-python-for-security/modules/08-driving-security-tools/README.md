# Module 08 — Driving Security Tools

*Module concept · [Go to the hands-on lab →](lab.md)*


**Python for Security** — *the best tool is the one you can script; scripting it means you can scale it.*

## Why this matters
Security platforms — MISP, VirusTotal, TheHive, Shodan — all have APIs. The analyst who uses
them through a browser clicks through one IOC at a time. The engineer who scripts them processes
hundreds of IOCs in the same time, logs every action, and can replay the run next week with the
same inputs. At Meridian scale, the difference is incident closure time.

## Objective
Use `pymisp` (the official MISP Python library) and direct HTTP to interact with a local mock
MISP instance: create an event, add attributes (IOCs), tag them, and then query a mock
VirusTotal API to pull enrichment and attach it back to the event.

## The core idea
`pymisp` is a thin wrapper around the MISP REST API — every operation it exposes is a structured
HTTP call with JSON. The reason to use `pymisp` rather than raw `httpx` for MISP operations is
that it handles the object model (events, attributes, tags) and the MISP-specific auth header
(`Authorization: <api_key>`) correctly, and it gives you Python objects rather than raw
dictionaries to work with. But the principle applies to any security platform: understand the
REST API first, then decide whether the library saves enough boilerplate to be worth the
dependency.

Creating a MISP event from an alert is a four-step operation: create the event (metadata — who
reported it, when, what threat level), add attributes (the actual IOCs with their type: `ip-dst`,
`domain`, `sha256`, `md5`), tag the event (TLP, MISP taxonomies, ATT&CK technique), and publish.
These four steps map directly to four API calls. The model for a "MISP attribute" is: type +
value + category + comment — every IOC in a MISP event is described by those four fields.

The integration pattern — query VirusTotal for an IOC, attach the VT verdict as a MISP comment
or a MISP object — is the same pattern used in automated enrichment pipelines across the
industry. The VT response tells you the detection ratio (how many engines flagged it); you attach
that as a `comment` or a `vt-report` object to the MISP attribute. The event then carries both
the raw IOC and the enrichment in one place, queryable and shareable via MISP's federated sync.

The operational discipline is: write automation that produces MISP events you would be
comfortable having a human review. Never create MISP events automatically at scale without
a human-in-the-loop gate, at least for the first run against a new data source. False-positive
IOC sharing (sending a known-good IP to your MISP community as malicious) is a trust problem
that is hard to undo.

## Learn (~2.5 hrs)

**MISP API and pymisp (~1.5 hrs)**
- [PyMISP — Official documentation](https://pymisp.readthedocs.io/en/latest/) — read "Getting started" and "Event management"; the examples are the fastest path to understanding the object model.
- [MISP REST API documentation](https://www.circl.lu/doc/misp/automation/) — skim "Authentication" and "Events"; this is the underlying API `pymisp` wraps; knowing it makes debugging easier.
- [MISP Taxonomies — circl.lu](https://www.circl.lu/doc/misp/taxonomy/) — understand TLP, PAP, and the MISP threat taxonomy; knowing which tags are standard is what separates a well-formed event from a private blob.

**VirusTotal API (~1 hr)**
- [VirusTotal API v3 — File/IP/Domain lookups](https://docs.virustotal.com/reference/ip-info) — read the response structure for an IP lookup: `last_analysis_stats`, `reputation`, `as_owner`; these are the fields you'll attach back to MISP.

## Key concepts
- MISP event anatomy: event → attributes → tags → publish
- MISP attribute type vocabulary: `ip-dst`, `domain`, `sha256`, `md5`, `url`
- `pymisp.MISPEvent` and `pymisp.MISPAttribute` as Python objects
- TLP and PAP tagging: standard community labels for sharing sensitivity
- Enrichment attach-back: VT verdict as MISP comment or object
- Human-in-the-loop gate: never publish automatically at scale without review

## AI acceleration
Ask a model to write the MISP event creation and attribute-adding code. It will get the
`pymisp` API mostly right but will often confuse `event.add_attribute()` with
`misp.add_attribute(event)` — one modifies the in-memory object, the other sends an API call.
Run its code against the mock MISP and check whether the event actually appears in the MISP UI.
If it doesn't, read the traceback — it will tell you exactly which API call failed.
