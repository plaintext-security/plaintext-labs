# Module 07 — Timeline Analysis

*Module concept · [Go to the hands-on lab →](lab.md)*


**Digital Forensics & IR** — *a timeline is the one artifact that turns a pile of evidence into a story.*

## Why this matters
Forensic artifacts are evidence, but they don't become a case until they're correlated. The Security event log, the browser history, the filesystem MAC times, the prefetch timestamps, and the memory acquisition time all record pieces of the same incident in different timezones, different timestamp formats, and different levels of granularity. A super-timeline stitches them together into a single, time-sorted view where every event from every source appears in order. It is the primary analytical tool for answering "what happened, in what order, and how long did it take?" — and it's often the evidence that turns a hypothesis into a finding.

## Objective
Build a multi-source forensic timeline using `log2timeline.py` (plaso) from a set of mixed artifact inputs; filter and pivot the timeline with `psort`; identify the key events in a Meridian Financial incident scenario; and produce a timeline extract that could form the basis of an incident report.

## The core idea
Think of a super-timeline as a database index on time. Plaso's `log2timeline.py` is a parser engine — it ingests almost any forensic artifact (disk images, EVTX files, browser history, prefetch, registry hives, system logs, web server logs) and emits a normalized stream of timestamped events in a standard format (Plaso's storage format, exportable to CSV, JSONL, or Timesketch). Each event has a source type, a timestamp, a description, and a set of attributes. The power is that all sources are normalized to UTC and sorted together, so the chain of events — attacker logged in at 02:10, browser search at 02:05, file access at 02:15, log cleared at 02:31 — becomes visible in one view instead of requiring you to correlate six separate tool outputs manually.

**The super-timeline's greatest contribution** is making gaps visible. When you look at timestamps from a single source, you see only what that source recorded. When you merge all sources and sort them, you see the *silences*: a 20-minute gap where a file should have been accessed but no event from any source shows activity. That gap is a hypothesis generator — was the attacker idle? Were they operating on a system that wasn't captured? Did they delete events that covered that window? The absence of evidence, made visible by a complete timeline, is itself evidence.

**Timestamp manipulation** is the most important caveat. NTFS records four timestamps per file in the `$STANDARD_INFORMATION` attribute (`$SI`) and a separate set in `$FILE_NAME` (`$FN`). The `$SI` timestamps can be modified by a user-mode process; `$FN` timestamps are updated by the kernel and are harder to manipulate. A common attacker technique called **timestomping** sets the `$SI` creation time to an implausibly old date to hide a newly created file in a sorted timeline. The defense is to compare `$SI` and `$FN` timestamps for the same file — a discrepancy is a red flag. The super-timeline built with plaso can surface both timestamp types for the same file entry, making this comparison possible.

**Timesketch** is the web-based analysis interface designed to work on plaso output. Where plaso is the ingestion and normalization engine, Timesketch is the pivot and query layer: filter by time window, search for a specific process name across all sources, annotate events as "confirmed C2 activity" or "false positive," and share the timeline with the IR team. For large incidents spanning millions of events, Timesketch's faceting and search are essential. For the lab, we'll work with CSV output from `psort`, which is equivalent for smaller datasets.

## Learn (~4 hrs)

**Plaso fundamentals (~2 hrs)**
- [log2timeline / plaso — GitHub documentation](https://github.com/log2timeline/plaso) — read the "Getting Started" and "Usage" sections; understand the three-step workflow: `log2timeline.py` (ingest), `psort.py` (filter/sort), `pstatus.py` (inspect).
- [plaso documentation — log2timeline.readthedocs.io](https://plaso.readthedocs.io/en/latest/) — the full plugin reference; skim the parser list to understand what artifact types plaso can ingest.

**Timesketch (~1 hr)**
- [Timesketch — GitHub](https://github.com/google/timesketch) — the README covers installation and the import workflow from plaso. Skim the "Usage" section.
- [Timesketch documentation — timesketch.org](https://timesketch.org/guides/user/upload-data/) — explains how to upload a plaso store and begin querying; read the "Searching" section.

**Timestamp forensics (~1 hr)**
- [MITRE ATT&CK T1070.006 — Timestomp](https://attack.mitre.org/techniques/T1070/006/) — the ATT&CK page for timestomping; understand what it does and the detection approaches.

## Key concepts
- Plaso's three-step workflow: `log2timeline.py` (ingest + parse) → `psort.py` (sort + filter + export) → analysis.
- All sources are normalized to UTC — timezone errors are the single most common mistake in timeline analysis.
- A super-timeline makes gaps visible — absence of events is an analytical signal, not just a gap.
- NTFS has two timestamp sets per file: `$SI` (user-modifiable) and `$FN` (kernel-updated). Discrepancy = possible timestomping.
- Timesketch is the web UI for querying and annotating plaso output at scale.
- Timeline events have source type, timestamp, and description — filter by all three to narrow hypotheses.
- The super-timeline is an IR report's primary evidentiary basis.

## AI acceleration
AI is highly effective at summarizing and interpreting timeline segments: paste a 50-event window and ask "what is the attacker doing in this sequence?" and you'll get a useful narrative draft. Where it fails: it cannot ingest plaso stores or generate real timestamps, and it will invent events that aren't in your data. Use it to draft the incident narrative from the timeline you've already built — then trace every sentence back to a specific event before finalizing the report.
